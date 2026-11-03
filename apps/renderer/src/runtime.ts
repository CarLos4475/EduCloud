import { getQuickJS, QuickJSContext, QuickJSRuntime } from "quickjs-emscripten";

export type Command = {
  type: string;
  id?: string;
  event?: string;
  value?: any;
};

export class ResourceVm {
  private commands: Command[] = [];
  private deadline = 0;
  private vm: QuickJSContext;
  private runtime: QuickJSRuntime;
  private constructor(
    module: Awaited<ReturnType<typeof getQuickJS>>,
    initial: Record<string, unknown>,
  ) {
    this.runtime = module.newRuntime();
    this.runtime.setMemoryLimit(32 * 1024 * 1024);
    this.runtime.setMaxStackSize(512 * 1024);
    this.runtime.setInterruptHandler(() => Date.now() > this.deadline);
    this.vm = this.runtime.newContext();
    const emit = this.vm.newFunction("_emit", (value) => {
      const text = this.vm.getString(value);
      if (text.length > 100_000 || this.commands.length >= 1000)
        throw new Error("Resource operation quota exceeded");
      this.commands.push(JSON.parse(text));
    });
    this.vm.setProp(this.vm.global, "_emit", emit);
    emit.dispose();
    this.execute(`
      let _state = ${JSON.stringify(initial)};
      const _handlers = Object.create(null);
      const send = (command) => _emit(JSON.stringify(command));
      const ui = Object.freeze({
        patch: (id,value) => send({type:'patch',id,value}),
        on: (id,event,handler) => { _handlers[id+':'+event] = handler; send({type:'listen',id,event}); },
        plot: (id,value) => send({type:'plot',id,value}),
        draw: (id,value) => send({type:'draw',id,value}),
        renderMath: (id,value) => send({type:'math',id,value}),
        mount: (id,value) => send({type:'mount',id,value}),
        animate: handler => { _handlers['animation:tick']=handler; send({type:'animate'}); }
      });
      const state = Object.freeze({read:()=>JSON.parse(JSON.stringify(_state)),write:value=>{_state=value;send({type:'state',value});}});
      function __dispatch(id,event,value) { const handler=_handlers[id+':'+event]; if(handler) handler(value); }
    `);
  }
  static async create(initial: Record<string, unknown> = {}) {
    return new ResourceVm(await getQuickJS(), initial);
  }
  execute(source: string): Command[] {
    this.commands = [];
    this.deadline = Date.now() + 100;
    const result = this.vm.evalCode(source);
    if (result.error) {
      const error = this.vm.dump(result.error);
      result.error.dispose();
      throw new Error(
        String(error?.message || "El recurso excedió sus límites."),
      );
    }
    result.value.dispose();
    return this.commands;
  }
  event(id: string, event: string, value: unknown) {
    return this.execute(
      `__dispatch(${JSON.stringify(id)},${JSON.stringify(event)},${JSON.stringify(value)});`,
    );
  }
  dispose() {
    this.vm.dispose();
    this.runtime.dispose();
  }
}

export async function runScript(
  source: string,
  initial: Record<string, unknown> = {},
) {
  const vm = await ResourceVm.create(initial);
  try {
    return vm.execute(source);
  } finally {
    vm.dispose();
  }
}
