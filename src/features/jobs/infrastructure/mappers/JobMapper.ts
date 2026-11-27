import type { JobOffer } from '../../domain/entities/JobOffer';
import type { EnglishLevel, WorkModality } from '../../domain/types';

/** Fila de `public.vacantes` tal como llega de Supabase (snake_case). */
export interface VacanteRow {
  id: string;
  titulo: string;
  empresa: string;
  modalidad: WorkModality;
  descripcion: string;
  requirements: string[];
  benefits: string[];
  stack_detectado: string[];
  nivel_ingles: EnglishLevel;
  experiencia_minima: number;
  ubicacion_texto: string;
  lat: number | null;
  lng: number | null;
  url_oferta: string;
  created_at: string;
}

/** Convierte una fila de `vacantes` en la entidad de dominio `JobOffer`. */
export function toJobOffer(row: VacanteRow): JobOffer {
  return {
    id: row.id,
    title: row.titulo,
    company: row.empresa,
    modality: row.modalidad,
    description: row.descripcion,
    requirements: row.requirements ?? [],
    benefits: row.benefits ?? [],
    stack: row.stack_detectado ?? [],
    englishLevel: row.nivel_ingles,
    isPracticante: (row.experiencia_minima ?? 1) === 0,
    locationText: row.ubicacion_texto,
    lat: row.lat ?? null,
    lng: row.lng ?? null,
    url: row.url_oferta,
    createdAt: row.created_at,
  };
}
