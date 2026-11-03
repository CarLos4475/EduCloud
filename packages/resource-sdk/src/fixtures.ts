export type InteractivePackage = {
  schemaVersion: 1;
  title: string;
  learningObjective: string;
  instructions: string;
  html: string;
  css: string;
  javascript: string;
  initialState: Record<string, unknown>;
  textAlternative: string;
  sourceRefs: unknown[];
  requestedCapabilities: string[];
};
const base = {
  schemaVersion: 1 as const,
  initialState: {},
  sourceRefs: [],
  requestedCapabilities: ["controls", "plot", "state"],
};
export const samples: InteractivePackage[] = [
  {
    ...base,
    title: "Explora una parábola",
    learningObjective:
      "Relacionar el coeficiente de x² con la forma de una parábola.",
    instructions:
      "Mueve el control para cambiar el coeficiente. Compara el valor de la función en x=2.",
    textAlternative:
      "Para f(x)=a x², f(2)=4a. Un coeficiente negativo abre la parábola hacia abajo.",
    html: '<label for="a">Coeficiente a</label><input id="a" type="range" min="-3" max="3" step="0.25" value="1"><p id="result"></p><div id="plot"></div>',
    css: "",
    javascript: `let a=Number(state.read().a || 1); function draw(){ui.patch('a',{value:String(a)});ui.patch('result',{text:'f(2) = '+(4*a)});ui.plot('plot',{points:Array.from({length:41},(_,i)=>{let x=(i-20)/5;return [x,a*x*x]}),label:'f(x) = '+a+' x²'});state.write({a});} ui.on('a','input',v=>{a=Number(v);draw()});draw();`,
  },
  {
    ...base,
    title: "Movimiento sin aceleración",
    learningObjective:
      "Explorar la relación entre distancia, velocidad y tiempo.",
    instructions:
      "Ajusta la velocidad para observar la posición a los cinco segundos.",
    textAlternative:
      "La posición es x = v t. En cinco segundos, una velocidad de 3 m/s produce un desplazamiento de 15 m.",
    html: '<label for="v">Velocidad (m/s)</label><input id="v" type="range" min="0" max="10" value="3"><p id="result"></p><canvas id="scene" width="600" height="160"></canvas><div id="plot"></div>',
    css: "",
    javascript: `let v=3; function draw(){ui.patch('result',{text:'A los 5 s: '+(v*5)+' m'});ui.draw('scene',[{op:'clear'},{op:'line',x:20,y:120,x2:580,y2:120},{op:'circle',x:30+v*48,y:90,r:18}]);ui.plot('plot',{points:Array.from({length:11},(_,t)=>[t,v*t]),label:'Posición en metros frente a tiempo en segundos'});}ui.on('v','input',value=>{v=Number(value);draw()});draw();`,
  },
  {
    ...base,
    title: "Ordena paso a paso",
    learningObjective:
      "Seguir los intercambios de un algoritmo de ordenamiento por burbuja.",
    instructions:
      "Avanza una comparación por vez y observa cómo cambia la lista.",
    textAlternative:
      "El algoritmo compara elementos vecinos e intercambia los que están fuera de orden, repitiendo hasta ordenar la lista.",
    html: '<p id="array"></p><button id="next" type="button">Siguiente comparación</button><p id="result"></p>',
    css: "",
    javascript: `const list=[5,2,4,1,3];let i=0,pass=0; function draw(){ui.patch('array',{text:list.join('   ·   ')});ui.patch('result',{text:pass>=4?'Lista ordenada.':'Comparación '+(i+1)+' de la pasada '+(pass+1)});}ui.on('next','click',()=>{if(pass>=4)return;if(list[i]>list[i+1]){const t=list[i];list[i]=list[i+1];list[i+1]=t;}i++;if(i>=4-pass){i=0;pass++;}draw();});draw();`,
  },
];
