// Músculos que trabaja cada ejercicio: [principales, secundarios].
// Los grupos son los del mapa muscular (js/vendor/muscle-map).

export const MUSCLE_NAMES = {
  chest: 'Pecho',
  shoulders: 'Hombros',
  biceps: 'Bíceps',
  triceps: 'Tríceps',
  forearms: 'Antebrazos',
  abs: 'Abdomen',
  obliques: 'Oblicuos',
  upper_back: 'Trapecio y espalda alta',
  lats: 'Dorsales',
  lower_back: 'Lumbares',
  glutes: 'Glúteos',
  quads: 'Cuádriceps',
  hamstrings: 'Femorales',
  calves: 'Pantorrillas',
};

// Se ven de espalda (el resto, de frente).
export const BACK_GROUPS = ['upper_back', 'lats', 'lower_back', 'triceps', 'glutes', 'hamstrings', 'calves'];
export const LOWER_GROUPS = ['glutes', 'quads', 'hamstrings', 'calves'];

// Para ejercicios propios: se deduce del grupo muscular elegido.
export const BY_CATEGORY = {
  Pecho: [['chest'], ['shoulders', 'triceps']],
  Espalda: [['lats', 'upper_back'], ['biceps']],
  Hombros: [['shoulders'], ['triceps']],
  'Bíceps': [['biceps'], ['forearms']],
  'Tríceps': [['triceps'], []],
  Antebrazo: [['forearms'], []],
  'Cuádriceps': [['quads'], ['glutes']],
  Isquios: [['hamstrings'], ['glutes']],
  'Glúteos': [['glutes'], ['hamstrings']],
  Pantorrillas: [['calves'], []],
  Abdomen: [['abs'], ['obliques']],
};

const PRESS_CHEST = [['chest'], ['shoulders', 'triceps']];
const FLY = [['chest'], ['shoulders']];
const PULLDOWN = [['lats'], ['biceps', 'upper_back']];
const ROW = [['lats', 'upper_back'], ['biceps', 'lower_back']];
const OVERHEAD = [['shoulders'], ['triceps', 'upper_back']];
const LATERAL = [['shoulders'], ['upper_back']];
const REAR_DELT = [['shoulders', 'upper_back'], []];
const CURL = [['biceps'], ['forearms']];
const TRICEPS = [['triceps'], []];
const SQUAT = [['quads', 'glutes'], ['hamstrings', 'lower_back', 'abs']];
const LUNGE = [['quads', 'glutes'], ['hamstrings', 'calves']];
const HINGE = [['hamstrings', 'glutes'], ['lower_back', 'forearms']];
const HAM_CURL = [['hamstrings'], ['calves']];
const GLUTE = [['glutes'], ['hamstrings']];
const CALF = [['calves'], []];
const ABS = [['abs'], ['obliques']];

export const EXERCISE_MUSCLES = {
  // Pecho
  'press-banca': PRESS_CHEST,
  'press-banca-mancuernas': PRESS_CHEST,
  'press-inclinado-barra': [['chest', 'shoulders'], ['triceps']],
  'press-inclinado-mancuernas': [['chest', 'shoulders'], ['triceps']],
  'press-declinado': PRESS_CHEST,
  'press-pecho-maquina': PRESS_CHEST,
  'press-inclinado-smith': [['chest', 'shoulders'], ['triceps']],
  'aperturas-mancuernas': FLY,
  'aperturas-inclinadas': FLY,
  'cruce-poleas': FLY,
  'cruce-poleas-bajo': FLY,
  'pec-deck': FLY,
  'fondos-pecho': [['chest', 'triceps'], ['shoulders']],
  flexiones: [['chest'], ['triceps', 'shoulders', 'abs']],
  pullover: [['chest', 'lats'], ['triceps']],

  // Espalda
  dominadas: [['lats'], ['biceps', 'upper_back', 'forearms']],
  'dominadas-supinas': [['lats', 'biceps'], ['upper_back', 'forearms']],
  'dominadas-lastradas': [['lats'], ['biceps', 'upper_back', 'forearms']],
  'jalon-pecho': PULLDOWN,
  'jalon-agarre-cerrado': PULLDOWN,
  'jalon-agarre-neutro': PULLDOWN,
  'remo-barra': ROW,
  'remo-pendlay': ROW,
  'remo-mancuerna': [['lats'], ['upper_back', 'biceps']],
  'remo-sentado-polea': [['lats', 'upper_back'], ['biceps']],
  'remo-t': ROW,
  'remo-maquina': [['lats', 'upper_back'], ['biceps']],
  'remo-pecho-apoyado': [['upper_back', 'lats'], ['biceps', 'shoulders']],
  'pullover-polea': [['lats'], ['triceps']],
  'peso-muerto': [['lower_back', 'glutes', 'hamstrings'], ['upper_back', 'quads', 'forearms']],
  'rack-pull': [['lower_back', 'upper_back'], ['glutes', 'forearms']],
  hiperextensiones: [['lower_back'], ['glutes', 'hamstrings']],
  'encogimientos-barra': [['upper_back'], ['forearms']],
  'encogimientos-mancuernas': [['upper_back'], ['forearms']],

  // Hombros
  'press-militar': [['shoulders'], ['triceps', 'upper_back', 'abs']],
  'press-hombro-mancuernas': OVERHEAD,
  'press-arnold': OVERHEAD,
  'press-hombro-maquina': OVERHEAD,
  'elevaciones-laterales': LATERAL,
  'elevaciones-laterales-polea': LATERAL,
  'elevaciones-laterales-maquina': LATERAL,
  'elevaciones-frontales': [['shoulders'], ['chest']],
  pajaros: REAR_DELT,
  'reverse-pec-deck': REAR_DELT,
  'face-pull': [['shoulders', 'upper_back'], ['biceps']],
  'remo-al-menton': [['shoulders', 'upper_back'], ['biceps']],

  // Bíceps
  'curl-barra': CURL,
  'curl-barra-z': CURL,
  'curl-mancuernas': CURL,
  'curl-martillo': [['biceps', 'forearms'], []],
  'curl-inclinado': CURL,
  'curl-predicador': CURL,
  'curl-concentrado': CURL,
  'curl-polea': CURL,
  'curl-bayesian': CURL,
  'curl-maquina': CURL,

  // Tríceps
  'press-frances': TRICEPS,
  'extension-polea': TRICEPS,
  'extension-polea-barra': TRICEPS,
  'extension-sobre-cabeza': TRICEPS,
  'extension-sobre-cabeza-polea': TRICEPS,
  'press-cerrado': [['triceps', 'chest'], ['shoulders']],
  'fondos-triceps': [['triceps'], ['chest', 'shoulders']],
  'fondos-banco': [['triceps'], ['shoulders', 'chest']],
  'patada-triceps': TRICEPS,
  'extension-triceps-maquina': TRICEPS,

  // Antebrazo
  'curl-muneca': [['forearms'], []],
  'curl-muneca-inverso': [['forearms'], []],
  'curl-inverso': [['forearms', 'biceps'], []],
  'paseo-granjero': [['forearms', 'upper_back'], ['abs', 'obliques', 'calves']],

  // Cuádriceps
  sentadilla: SQUAT,
  'sentadilla-frontal': [['quads'], ['glutes', 'abs', 'upper_back']],
  'sentadilla-hack': [['quads'], ['glutes']],
  'sentadilla-smith': [['quads', 'glutes'], ['hamstrings']],
  'sentadilla-goblet': [['quads', 'glutes'], ['abs']],
  'sentadilla-bulgara': LUNGE,
  prensa: [['quads', 'glutes'], ['hamstrings']],
  'extension-cuadriceps': [['quads'], []],
  zancadas: LUNGE,
  'zancadas-caminando': LUNGE,
  'pendulum-squat': [['quads'], ['glutes']],
  'step-up': LUNGE,

  // Isquios
  'peso-muerto-rumano': HINGE,
  'peso-muerto-rumano-mancuernas': HINGE,
  'peso-muerto-piernas-rigidas': HINGE,
  'curl-femoral-tumbado': HAM_CURL,
  'curl-femoral-sentado': HAM_CURL,
  'buenos-dias': [['hamstrings', 'lower_back'], ['glutes']],
  'nordic-curl': HAM_CURL,

  // Glúteos
  'hip-thrust': [['glutes'], ['hamstrings', 'quads']],
  'hip-thrust-maquina': [['glutes'], ['hamstrings']],
  'prensa-gluteos': [['glutes', 'quads'], ['hamstrings']],
  'puente-gluteo': GLUTE,
  'patada-gluteo-polea': GLUTE,
  'abductores-maquina': [['glutes'], []],
  // El mapa no separa los aductores: se marca la zona del muslo.
  'aductores-maquina': [['quads'], ['glutes']],
  'peso-muerto-sumo': [['glutes', 'quads', 'hamstrings'], ['lower_back', 'upper_back', 'forearms']],

  // Pantorrillas
  'elevacion-talones-pie': CALF,
  'elevacion-talones-sentado': CALF,
  'elevacion-talones-prensa': CALF,
  'elevacion-talones-smith': CALF,

  // Abdomen
  crunch: ABS,
  'crunch-polea': ABS,
  'crunch-maquina': ABS,
  plancha: [['abs'], ['obliques', 'shoulders', 'glutes']],
  'plancha-lateral': [['obliques'], ['abs', 'glutes']],
  'elevacion-piernas-colgado': [['abs'], ['obliques', 'forearms']],
  'elevacion-piernas-banco': ABS,
  'rueda-abdominal': [['abs'], ['lats', 'shoulders', 'obliques']],
  'russian-twist': [['obliques'], ['abs']],
  'pallof-press': [['obliques', 'abs'], []],
  woodchopper: [['obliques'], ['abs', 'shoulders']],
};
