import { useEffect, useMemo, useState } from 'react';
import * as Location from 'expo-location';

import type { Coordinates } from './distance';

export type LocationStatus = 'granted' | 'denied' | 'undetermined';

export interface UseDeviceLocation {
  coords: Coordinates | null;
  status: LocationStatus;
}

/**
 * Pide el permiso de ubicación en primer plano una sola vez al montar y lee
 * la posición actual. Si falla, devuelve coords null para usar el orden neutral.
 */
export function useDeviceLocation(): UseDeviceLocation {
  const [coords, setCoords] = useState<Coordinates | null>(null);
  const [status, setStatus] = useState<LocationStatus>('undetermined');

  useEffect(() => {
    let cancelled = false;

    async function readLocation(): Promise<void> {
      try {
        const permission = await Location.requestForegroundPermissionsAsync();
        if (cancelled) return;

        if (permission.status === Location.PermissionStatus.UNDETERMINED) {
          setStatus('undetermined');
          return;
        }

        if (permission.status !== Location.PermissionStatus.GRANTED) {
          setStatus('denied');
          return;
        }

        setStatus('granted');

        const position = await Location.getCurrentPositionAsync({});
        if (cancelled) return;

        setCoords({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      } catch (error) {
        if (!cancelled) {
          console.warn('No se pudo obtener la ubicación del dispositivo:', error);
        }
      }
    }

    readLocation();

    return () => {
      cancelled = true;
    };
  }, []);

  return useMemo(() => ({ coords, status }), [coords, status]);
}
