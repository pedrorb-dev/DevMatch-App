import type { JobOffer } from '../../domain/entities/JobOffer';

/**
 * Devuelve una fecha ISO relativa a hoy. Se usa para que el filtro
 * "Nuevos hoy" del Feed siga funcionando sin fechas fijas.
 */
const daysAgo = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString();
};

export const mockJobs: JobOffer[] = [
  {
    id: 'devmatch-01',
    title: 'Desarrollador Angular Senior',
    company: 'Nexo Digital',
    modality: 'Remoto',
    description:
      'Desarrollo de aplicaciones web con Angular y TypeScript. Equipo distribuido en LATAM.',
    stack: ['Angular', 'TypeScript', 'RxJS'],
    englishLevel: 'B2',
    isPracticante: false,
    locationText: 'Remoto (LATAM)',
    url: 'https://example.com/jobs/devmatch-01',
    createdAt: daysAgo(0),
  },
  {
    id: 'devmatch-02',
    title: 'Backend Java Spring Boot',
    company: 'Fintech Andina',
    modality: 'Híbrido',
    description:
      'Construcción de servicios REST con Spring Boot para una plataforma financiera.',
    stack: ['Java', 'Spring Boot', 'PostgreSQL'],
    englishLevel: 'B1',
    isPracticante: false,
    locationText: 'Ciudad de México',
    url: 'https://example.com/jobs/devmatch-02',
    createdAt: daysAgo(0),
  },
  {
    id: 'devmatch-03',
    title: 'Practicante de Desarrollo Web',
    company: 'Startup Lab',
    modality: 'Presencial',
    description:
      'Apoyo en el desarrollo de interfaces con React y consumo de APIs con Node.js.',
    stack: ['React', 'Node.js', 'JavaScript'],
    englishLevel: 'A2',
    isPracticante: true,
    locationText: 'Guadalajara',
    url: 'https://example.com/jobs/devmatch-03',
    createdAt: daysAgo(0),
  },
  {
    id: 'devmatch-04',
    title: 'React Native Developer',
    company: 'MoviApps',
    modality: 'Remoto',
    description:
      'Mantenimiento y nuevas features en una app móvil de entregas con React Native.',
    stack: ['React Native', 'TypeScript'],
    englishLevel: 'B2',
    isPracticante: false,
    locationText: 'Remoto',
    url: 'https://example.com/jobs/devmatch-04',
    createdAt: daysAgo(0),
  },
  {
    id: 'devmatch-05',
    title: 'Trainee Backend Python',
    company: 'DataBridge',
    modality: 'Híbrido',
    description:
      'Programa de formación para recién egresados en desarrollo backend con Python.',
    stack: ['Python', 'FastAPI'],
    englishLevel: 'B1',
    isPracticante: true,
    locationText: 'Monterrey',
    url: 'https://example.com/jobs/devmatch-05',
    createdAt: daysAgo(0),
  },
  {
    id: 'devmatch-06',
    title: 'Full Stack .NET',
    company: 'Grupo Cero',
    modality: 'Presencial',
    description:
      'Desarrollo end-to-end de soluciones empresariales con .NET y SQL Server.',
    stack: ['C#', '.NET', 'SQL Server'],
    englishLevel: 'B1',
    isPracticante: false,
    locationText: 'Querétaro',
    url: 'https://example.com/jobs/devmatch-06',
    createdAt: daysAgo(1),
  },
  {
    id: 'devmatch-07',
    title: 'Ingeniero DevOps',
    company: 'CloudNova',
    modality: 'Remoto',
    description:
      'Automatización de pipelines CI/CD y gestión de infraestructura en AWS.',
    stack: ['AWS', 'Docker', 'Kubernetes'],
    englishLevel: 'C1',
    isPracticante: false,
    locationText: 'Remoto',
    url: 'https://example.com/jobs/devmatch-07',
    createdAt: daysAgo(2),
  },
  {
    id: 'devmatch-08',
    title: 'Desarrollador Frontend Vue',
    company: 'Pixel Studio',
    modality: 'Híbrido',
    description:
      'Creación de interfaces de usuario con Vue.js para productos de e-commerce.',
    stack: ['Vue.js', 'JavaScript'],
    englishLevel: 'A2',
    isPracticante: false,
    locationText: 'Puebla',
    url: 'https://example.com/jobs/devmatch-08',
    createdAt: daysAgo(3),
  },
  {
    id: 'devmatch-09',
    title: 'Becario QA Automation',
    company: 'TestWorks',
    modality: 'Presencial',
    description:
      'Automatización de pruebas funcionales con Selenium y Java bajo supervisión.',
    stack: ['Selenium', 'Java'],
    englishLevel: 'A2',
    isPracticante: true,
    locationText: 'Ciudad de México',
    url: 'https://example.com/jobs/devmatch-09',
    createdAt: daysAgo(4),
  },
  {
    id: 'devmatch-10',
    title: 'Backend Node.js',
    company: 'LogiTech',
    modality: 'Remoto',
    description:
      'Desarrollo de microservicios con Node.js y MongoDB para logística.',
    stack: ['Node.js', 'Express', 'MongoDB'],
    englishLevel: 'B2',
    isPracticante: false,
    locationText: 'Remoto',
    url: 'https://example.com/jobs/devmatch-10',
    createdAt: daysAgo(5),
  },
  {
    id: 'devmatch-11',
    title: 'Practicante Data Science',
    company: 'Insight AI',
    modality: 'Híbrido',
    description:
      'Análisis de datos y modelos básicos de machine learning con Python.',
    stack: ['Python', 'Pandas', 'scikit-learn'],
    englishLevel: 'B1',
    isPracticante: true,
    locationText: 'Monterrey',
    url: 'https://example.com/jobs/devmatch-11',
    createdAt: daysAgo(6),
  },
  {
    id: 'devmatch-12',
    title: 'Android Developer Kotlin',
    company: 'AppFactory',
    modality: 'Presencial',
    description:
      'Desarrollo de aplicaciones Android nativas con Kotlin y Jetpack Compose.',
    stack: ['Kotlin', 'Android', 'Jetpack Compose'],
    englishLevel: 'B2',
    isPracticante: false,
    locationText: 'Guadalajara',
    url: 'https://example.com/jobs/devmatch-12',
    createdAt: daysAgo(8),
  },
  {
    id: 'devmatch-13',
    title: 'Ingeniero de Software',
    company: 'GlobalSoft',
    modality: 'Remoto',
    description:
      'Desarrollo de aplicaciones empresariales con Java, Angular y Spring Boot.',
    stack: ['Java', 'Angular', 'Spring Boot'],
    englishLevel: 'C1',
    isPracticante: false,
    locationText: 'Remoto',
    url: 'https://example.com/jobs/devmatch-13',
    createdAt: daysAgo(10),
  },
  {
    id: 'devmatch-14',
    title: 'Junior Frontend React',
    company: 'WebMakers',
    modality: 'Híbrido',
    description:
      'Primer empleo en desarrollo frontend con React y JavaScript moderno.',
    stack: ['React', 'JavaScript'],
    englishLevel: 'A2',
    isPracticante: false,
    locationText: 'León',
    url: 'https://example.com/jobs/devmatch-14',
    createdAt: daysAgo(13),
  },
];
