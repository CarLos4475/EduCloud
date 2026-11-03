import { ResourceVm } from "./runtime";
let vm: ResourceVm | null = null;
self.onmessage = async (event) => {
  try {
    const message = event.data;
    if (message.type === "load") {
      vm?.dispose();
      vm = await ResourceVm.create(message.state || {});
      self.postMessage({
        type: "commands",
        commands: vm.execute(message.code),
      });
    } else if (message.type === "event" && vm) {
      self.postMessage({
        type: "commands",
        commands: vm.event(message.id, message.event, message.value),
      });
    }
  } catch {
    vm?.dispose();
    vm = null;
    self.postMessage({
      type: "error",
      message:
        "El recurso se detuvo al alcanzar un límite o una instrucción no válida. Puedes reiniciarlo.",
    });
  }
};
