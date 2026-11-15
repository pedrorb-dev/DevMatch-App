import type { EnglishLevel, WorkModality } from '../types';

export interface JobOffer {
  id: string;
  title: string;
  company: string;
  modality: WorkModality;
  description: string;
  requirements: string[];
  benefits: string[];
  stack: string[];
  englishLevel: EnglishLevel;
  isPracticante: boolean;
  locationText: string;
  url: string;
  createdAt: string;
}
