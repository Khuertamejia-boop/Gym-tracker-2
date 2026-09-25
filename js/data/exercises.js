// Catálogo base de ejercicios: [id, nombre, grupo muscular, equipo, alias de búsqueda]
export const MUSCLES = [
  'Pecho', 'Espalda', 'Hombros', 'Bíceps', 'Tríceps', 'Antebrazo',
  'Cuádriceps', 'Isquios', 'Glúteos', 'Pantorrillas', 'Abdomen',
];

const RAW = [
  // Pecho
  ['press-banca', 'Press de banca con barra', 'Pecho', 'Barra'],
  ['press-banca-mancuernas', 'Press de banca con mancuernas', 'Pecho', 'Mancuernas'],
  ['press-inclinado-barra', 'Press inclinado con barra', 'Pecho', 'Barra'],
  ['press-inclinado-mancuernas', 'Press inclinado con mancuernas', 'Pecho', 'Mancuernas'],
  ['press-declinado', 'Press declinado con barra', 'Pecho', 'Barra'],
  ['press-pecho-maquina', 'Press de pecho en máquina', 'Pecho', 'Máquina', 'press en maquina'],
  ['press-inclinado-smith', 'Press inclinado en Smith', 'Pecho', 'Smith'],
  ['aperturas-mancuernas', 'Aperturas con mancuernas', 'Pecho', 'Mancuernas'],
  ['aperturas-inclinadas', 'Aperturas inclinadas con mancuernas', 'Pecho', 'Mancuernas'],
  ['cruce-poleas', 'Cruce de poleas', 'Pecho', 'Polea'],
  ['cruce-poleas-bajo', 'Cruce de poleas de abajo hacia arriba', 'Pecho', 'Polea'],
  ['pec-deck', 'Pec deck (contractor)', 'Pecho', 'Máquina', 'peck deck mariposa'],
  ['fondos-pecho', 'Fondos en paralelas (pecho)', 'Pecho', 'Peso corporal'],
  ['flexiones', 'Flexiones de brazos', 'Pecho', 'Peso corporal'],
  ['pullover', 'Pullover con mancuerna', 'Pecho', 'Mancuernas'],

  // Espalda
  ['dominadas', 'Dominadas', 'Espalda', 'Peso corporal'],
  ['dominadas-supinas', 'Dominadas supinas (chin-ups)', 'Espalda', 'Peso corporal'],
  ['dominadas-lastradas', 'Dominadas lastradas', 'Espalda', 'Peso corporal'],
  ['jalon-pecho', 'Jalón al pecho', 'Espalda', 'Polea'],
  ['jalon-agarre-cerrado', 'Jalón con agarre cerrado', 'Espalda', 'Polea'],
  ['jalon-agarre-neutro', 'Jalón al pecho con agarre neutro', 'Espalda', 'Polea', 'jalon neutro'],
  ['remo-barra', 'Remo con barra', 'Espalda', 'Barra'],
  ['remo-pendlay', 'Remo Pendlay', 'Espalda', 'Barra'],
  ['remo-mancuerna', 'Remo con mancuerna a una mano', 'Espalda', 'Mancuernas'],
  ['remo-sentado-polea', 'Remo sentado en polea', 'Espalda', 'Polea'],
  ['remo-t', 'Remo en T', 'Espalda', 'Barra'],
  ['remo-maquina', 'Remo en máquina', 'Espalda', 'Máquina'],
  ['remo-pecho-apoyado', 'Remo con pecho apoyado', 'Espalda', 'Mancuernas'],
  ['pullover-polea', 'Pullover en polea alta', 'Espalda', 'Polea'],
  ['peso-muerto', 'Peso muerto', 'Espalda', 'Barra'],
  ['rack-pull', 'Rack pull', 'Espalda', 'Barra'],
  ['hiperextensiones', 'Hiperextensiones', 'Espalda', 'Peso corporal'],
  ['encogimientos-barra', 'Encogimientos con barra', 'Espalda', 'Barra'],
  ['encogimientos-mancuernas', 'Encogimientos con mancuernas', 'Espalda', 'Mancuernas'],

  // Hombros
  ['press-militar', 'Press militar con barra', 'Hombros', 'Barra'],
  ['press-hombro-mancuernas', 'Press de hombro con mancuernas', 'Hombros', 'Mancuernas'],
  ['press-arnold', 'Press Arnold', 'Hombros', 'Mancuernas'],
  ['press-hombro-maquina', 'Press de hombro en máquina', 'Hombros', 'Máquina', 'press militar en maquina'],
  ['elevaciones-laterales', 'Elevaciones laterales con mancuernas', 'Hombros', 'Mancuernas'],
  ['elevaciones-laterales-polea', 'Elevaciones laterales en polea', 'Hombros', 'Polea'],
  ['elevaciones-laterales-maquina', 'Elevaciones laterales en máquina', 'Hombros', 'Máquina'],
  ['elevaciones-frontales', 'Elevaciones frontales', 'Hombros', 'Mancuernas'],
  ['pajaros', 'Pájaros (elevaciones posteriores)', 'Hombros', 'Mancuernas'],
  ['reverse-pec-deck', 'Pec deck invertido', 'Hombros', 'Máquina'],
  ['face-pull', 'Face pull', 'Hombros', 'Polea'],
  ['remo-al-menton', 'Remo al mentón', 'Hombros', 'Barra'],

  // Bíceps
  ['curl-barra', 'Curl con barra', 'Bíceps', 'Barra'],
  ['curl-barra-z', 'Curl con barra Z', 'Bíceps', 'Barra'],
  ['curl-mancuernas', 'Curl con mancuernas', 'Bíceps', 'Mancuernas'],
  ['curl-martillo', 'Curl martillo', 'Bíceps', 'Mancuernas'],
  ['curl-inclinado', 'Curl inclinado con mancuernas', 'Bíceps', 'Mancuernas'],
  ['curl-predicador', 'Curl en banco Scott (predicador)', 'Bíceps', 'Barra'],
  ['curl-concentrado', 'Curl concentrado', 'Bíceps', 'Mancuernas'],
  ['curl-polea', 'Curl en polea', 'Bíceps', 'Polea'],
  ['curl-bayesian', 'Curl bayesiano en polea', 'Bíceps', 'Polea'],
  ['curl-maquina', 'Curl de bíceps en máquina', 'Bíceps', 'Máquina'],

  // Tríceps
  ['press-frances', 'Press francés', 'Tríceps', 'Barra', 'skull crusher rompecraneos'],
  ['extension-polea', 'Extensión de tríceps en polea (cuerda)', 'Tríceps', 'Polea'],
  ['extension-polea-barra', 'Extensión de tríceps en polea (barra)', 'Tríceps', 'Polea', 'jalon de triceps con barra'],
  ['extension-sobre-cabeza', 'Extensión sobre la cabeza con mancuerna', 'Tríceps', 'Mancuernas'],
  ['extension-sobre-cabeza-polea', 'Extensión sobre la cabeza en polea', 'Tríceps', 'Polea'],
  ['press-cerrado', 'Press de banca agarre cerrado', 'Tríceps', 'Barra'],
  ['fondos-triceps', 'Fondos en paralelas (tríceps)', 'Tríceps', 'Peso corporal'],
  ['fondos-banco', 'Fondos en banco', 'Tríceps', 'Peso corporal'],
  ['patada-triceps', 'Patada de tríceps', 'Tríceps', 'Mancuernas'],
  ['extension-triceps-maquina', 'Extensión de tríceps en máquina', 'Tríceps', 'Máquina'],

  // Antebrazo
  ['curl-muneca', 'Curl de muñeca', 'Antebrazo', 'Barra'],
  ['curl-muneca-inverso', 'Curl de muñeca inverso', 'Antebrazo', 'Barra'],
  ['curl-inverso', 'Curl inverso con barra', 'Antebrazo', 'Barra'],
  ['paseo-granjero', 'Paseo del granjero', 'Antebrazo', 'Mancuernas'],

  // Cuádriceps
  ['sentadilla', 'Sentadilla con barra', 'Cuádriceps', 'Barra'],
  ['sentadilla-frontal', 'Sentadilla frontal', 'Cuádriceps', 'Barra'],
  ['sentadilla-hack', 'Sentadilla hack', 'Cuádriceps', 'Máquina', 'sentadilla lat'],
  ['sentadilla-smith', 'Sentadilla en Smith · cuádriceps', 'Cuádriceps', 'Smith'],
  ['sentadilla-goblet', 'Sentadilla goblet', 'Cuádriceps', 'Mancuernas'],
  ['sentadilla-bulgara', 'Sentadilla búlgara · cuádriceps', 'Cuádriceps', 'Mancuernas'],
  ['prensa', 'Prensa de piernas · cuádriceps', 'Cuádriceps', 'Máquina'],
  ['extension-cuadriceps', 'Extensión de cuádriceps', 'Cuádriceps', 'Máquina'],
  ['zancadas', 'Zancadas (estocadas)', 'Cuádriceps', 'Mancuernas'],
  ['zancadas-caminando', 'Zancadas caminando', 'Cuádriceps', 'Mancuernas'],
  ['pendulum-squat', 'Sentadilla péndulo', 'Cuádriceps', 'Máquina'],
  ['step-up', 'Step-up (subida al cajón)', 'Cuádriceps', 'Mancuernas', 'subidas cajon unilateral'],

  // Isquios
  ['peso-muerto-rumano', 'Peso muerto rumano', 'Isquios', 'Barra'],
  ['peso-muerto-rumano-mancuernas', 'Peso muerto rumano con mancuernas', 'Isquios', 'Mancuernas'],
  ['peso-muerto-piernas-rigidas', 'Peso muerto con piernas rígidas', 'Isquios', 'Barra'],
  ['curl-femoral-tumbado', 'Curl femoral tumbado', 'Isquios', 'Máquina'],
  ['curl-femoral-sentado', 'Curl femoral sentado', 'Isquios', 'Máquina'],
  ['buenos-dias', 'Buenos días', 'Isquios', 'Barra'],
  ['nordic-curl', 'Curl nórdico', 'Isquios', 'Peso corporal'],

  // Glúteos
  ['hip-thrust', 'Hip thrust con barra', 'Glúteos', 'Barra'],
  ['hip-thrust-maquina', 'Hip thrust en máquina', 'Glúteos', 'Máquina'],
  ['prensa-gluteos', 'Prensa de piernas · glúteos', 'Glúteos', 'Máquina', 'prensa pies altos enfocada'],
  ['sentadilla-bulgara-gluteos', 'Sentadilla búlgara · glúteos', 'Glúteos', 'Mancuernas', 'torso inclinado enfocada'],
  ['sentadilla-smith-gluteos', 'Sentadilla en Smith · glúteos', 'Glúteos', 'Smith', 'pies adelantados enfocada'],
  ['puente-gluteo', 'Puente de glúteo', 'Glúteos', 'Peso corporal'],
  ['patada-gluteo-polea', 'Patada de glúteo en polea', 'Glúteos', 'Polea'],
  ['abductores-maquina', 'Abducción de cadera en máquina', 'Glúteos', 'Máquina'],
  ['aductores-maquina', 'Aducción de cadera en máquina', 'Glúteos', 'Máquina'],
  ['peso-muerto-sumo', 'Peso muerto sumo', 'Glúteos', 'Barra'],

  // Pantorrillas
  ['elevacion-talones-pie', 'Elevación de talones de pie', 'Pantorrillas', 'Máquina', 'gemelos'],
  ['elevacion-talones-sentado', 'Elevación de talones sentado', 'Pantorrillas', 'Máquina', 'gemelos sentado'],
  ['elevacion-talones-prensa', 'Elevación de talones en prensa', 'Pantorrillas', 'Máquina', 'gemelos'],
  ['elevacion-talones-smith', 'Elevación de talones en Smith', 'Pantorrillas', 'Smith', 'gemelos'],

  // Abdomen
  ['crunch', 'Crunch abdominal', 'Abdomen', 'Peso corporal', 'abdominales'],
  ['crunch-polea', 'Crunch en polea', 'Abdomen', 'Polea'],
  ['crunch-maquina', 'Crunch en máquina', 'Abdomen', 'Máquina'],
  ['plancha', 'Plancha', 'Abdomen', 'Peso corporal'],
  ['plancha-lateral', 'Plancha lateral', 'Abdomen', 'Peso corporal'],
  ['elevacion-piernas-colgado', 'Elevación de piernas colgado', 'Abdomen', 'Peso corporal'],
  ['elevacion-piernas-banco', 'Elevación de piernas en banco', 'Abdomen', 'Peso corporal'],
  ['rueda-abdominal', 'Rueda abdominal', 'Abdomen', 'Otro'],
  ['russian-twist', 'Giros rusos', 'Abdomen', 'Peso corporal'],
  ['pallof-press', 'Press Pallof', 'Abdomen', 'Polea'],
  ['woodchopper', 'Leñador en polea', 'Abdomen', 'Polea'],
];

// Ejercicios con variantes de enfoque: al buscarlos aparece uno solo y luego se elige el enfoque.
export const FAMILIES = {
  prensa: { name: 'Prensa de piernas', variants: [['prensa', 'Cuádriceps'], ['prensa-gluteos', 'Glúteos']] },
  bulgara: { name: 'Sentadilla búlgara', variants: [['sentadilla-bulgara', 'Cuádriceps'], ['sentadilla-bulgara-gluteos', 'Glúteos']] },
  smith: { name: 'Sentadilla en Smith', variants: [['sentadilla-smith', 'Cuádriceps'], ['sentadilla-smith-gluteos', 'Glúteos']] },
};
const FAMILY_OF = Object.fromEntries(Object.entries(FAMILIES).flatMap(([key, f]) => f.variants.map(([id]) => [id, key])));

// Ejercicios que se pueden registrar por lado (izquierda / derecha).
// true = activado por defecto (se hacen siempre de uno en uno); false = opcional.
export const UNILATERAL = {
  'step-up': true,
  'sentadilla-bulgara': true,
  'sentadilla-bulgara-gluteos': true,
  zancadas: false,
  'zancadas-caminando': false,
  'jalon-pecho': false,
  'jalon-agarre-cerrado': false,
  'jalon-agarre-neutro': false,
  'remo-mancuerna': true,
  'remo-sentado-polea': false,
  'curl-mancuernas': false,
  'curl-martillo': false,
  'curl-concentrado': true,
  'curl-polea': false,
  'extension-polea': false,
  'extension-sobre-cabeza': false,
  'patada-triceps': false,
  'elevaciones-laterales': false,
  'elevaciones-laterales-polea': false,
  'extension-cuadriceps': false,
  'curl-femoral-tumbado': false,
  'curl-femoral-sentado': false,
  prensa: false,
  'prensa-gluteos': false,
  'peso-muerto-rumano-mancuernas': false,
  'patada-gluteo-polea': true,
  'elevacion-talones-pie': false,
};

export const BASE_EXERCISES = RAW.map(([id, name, muscle, equipment, aliases = '']) => ({ id, name, muscle, equipment, aliases, family: FAMILY_OF[id] }));
