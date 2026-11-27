import { useEffect, useState } from 'react';
import {
  Alert,
  Dimensions,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import {
  Gesture,
  GestureDetector,
  GestureHandlerRootView,
  ScrollView,
} from 'react-native-gesture-handler';
import Animated, {
  interpolate,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

import {
  canUseRemotePush,
  registerForPushNotificationsAsync,
  sendLocalTestNotification,
  sendTestPushNotification,
} from '@/core/push/registerPushToken';
import { useTheme } from '@/core/theme/ThemeContext';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from './ProfileForm';

const AnimatedScrollView = Animated.createAnimatedComponent(ScrollView);

const SCREEN_HEIGHT = Dimensions.get('window').height;
const CLOSE_THRESHOLD = 140;
const CLOSE_VELOCITY = 1200;

interface ProfileDevMenuProps {
  visible: boolean;
  initialProfile: UserProfile;
  onSubmit: (profile: UserProfile) => Promise<void> | void;
  onClose: () => void;
}

export function ProfileDevMenu({ visible, initialProfile, onSubmit, onClose }: ProfileDevMenuProps) {
  const { colors, isDark, toggleMode, spacing, fontSize, fontWeight } = useTheme();
  const translateY = useSharedValue(0);
  const scrollY = useSharedValue(0);
  const sheetHeight = useSharedValue(SCREEN_HEIGHT);
  const [isTestingPush, setIsTestingPush] = useState(false);
  const remotePushAvailable = canUseRemotePush();

  useEffect(() => {
    if (visible) {
      translateY.value = 0;
      scrollY.value = 0;
    }
  }, [scrollY, translateY, visible]);

  const closeSheet = () => {
    onClose();
  };

  const handleTestPush = async () => {
    setIsTestingPush(true);
    try {
      if (!remotePushAvailable) {
        await sendLocalTestNotification();
        Alert.alert(
          'Notificación local enviada',
          'Expo Go solo admite notificaciones locales. Para push remoto usa un development build.',
        );
        return;
      }

      const token = await registerForPushNotificationsAsync();
      if (!token) {
        Alert.alert(
          'Push no disponible',
          'En Android se necesita un development build (Expo Go no soporta push remoto desde SDK 53). Revisa también los permisos y el projectId de EAS.',
        );
        return;
      }

      await sendTestPushNotification(token);
      Alert.alert('Push enviado', 'Deberías recibir la notificación de prueba en este dispositivo.');
    } catch (error) {
      Alert.alert('Error al probar el push', error instanceof Error ? error.message : String(error));
    } finally {
      setIsTestingPush(false);
    }
  };

  const handleScroll = (event: { nativeEvent: { contentOffset: { y: number } } }) => {
    scrollY.value = Math.max(0, event.nativeEvent.contentOffset.y);
  };

  const nativeScrollGesture = Gesture.Native();

  const panGesture = Gesture.Pan()
    .activeOffsetY([10, 9999])
    .failOffsetY([-9999, -10])
    .simultaneousWithExternalGesture(nativeScrollGesture)
    .onUpdate((event) => {
      if (scrollY.value <= 0 && event.translationY > 0) {
        translateY.value = event.translationY;
      } else if (scrollY.value <= 0 && event.translationY <= 0) {
        translateY.value = 0;
      }
      // If content is scrolled down, keep sheet in place and let scroll handle the gesture.
      if (scrollY.value > 0) {
        translateY.value = 0;
      }
    })
    .onEnd((event) => {
      if (scrollY.value > 0) {
        translateY.value = withSpring(0, { damping: 20, stiffness: 220 });
        return;
      }

      const shouldClose =
        translateY.value > CLOSE_THRESHOLD || event.velocityY > CLOSE_VELOCITY;

      if (shouldClose) {
        const target = sheetHeight.value || SCREEN_HEIGHT;
        translateY.value = withTiming(target, { duration: 220 }, (finished) => {
          if (finished) {
            runOnJS(closeSheet)();
          }
        });
      } else {
        translateY.value = withSpring(0, { damping: 20, stiffness: 220 });
      }
    });

  const composedGesture = Gesture.Simultaneous(panGesture, nativeScrollGesture);

  const sheetAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: translateY.value }],
  }));

  const backdropAnimatedStyle = useAnimatedStyle(() => ({
    opacity: interpolate(translateY.value, [0, sheetHeight.value || SCREEN_HEIGHT], [1, 0], 'clamp'),
  }));

  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onClose}>
      <GestureHandlerRootView style={styles.modalRoot}>
        <View style={styles.overlay}>
          <Animated.View style={[styles.backdrop, backdropAnimatedStyle]}>
            <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityRole="button" />
          </Animated.View>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.sheetContainer}
          >
            <GestureDetector gesture={composedGesture}>
              <Animated.View
                style={[styles.sheet, { backgroundColor: colors.surface }, sheetAnimatedStyle]}
                onLayout={(event) => {
                  sheetHeight.value = event.nativeEvent.layout.height;
                }}
              >
                <View style={[styles.handle, { backgroundColor: colors.border }]} />
                <Text style={[styles.title, { color: colors.text }]}>Editar perfil</Text>

                <AnimatedScrollView
                  contentContainerStyle={styles.content}
                  keyboardShouldPersistTaps="handled"
                  showsVerticalScrollIndicator={false}
                  onScroll={handleScroll}
                  scrollEventThrottle={16}
                  bounces={false}
                >
                  <View
                    style={[
                      styles.themeRow,
                      {
                        borderColor: colors.border,
                        backgroundColor: colors.background,
                        marginTop: spacing.sm,
                        marginBottom: spacing.md,
                      },
                    ]}
                  >
                    <View style={styles.themeRowText}>
                      <Text style={{ fontSize: fontSize.md, fontWeight: fontWeight.semibold, color: colors.text }}>
                        Modo oscuro
                      </Text>
                    </View>
                    <Switch
                      value={isDark}
                      onValueChange={toggleMode}
                      trackColor={{ false: colors.border, true: colors.primary }}
                      thumbColor={colors.white}
                      accessibilityRole="switch"
                      accessibilityLabel="Modo oscuro"
                    />
                  </View>

                  <ProfileForm
                    initialProfile={initialProfile}
                    submitLabel="Guardar"
                    onSubmit={onSubmit}
                  />

                  <Pressable style={styles.cancelButton} onPress={onClose} accessibilityRole="button">
                    <Text style={[styles.cancelButtonText, { color: colors.textSecondary }]}>Cancelar</Text>
                  </Pressable>
                </AnimatedScrollView>
              </Animated.View>
            </GestureDetector>
          </KeyboardAvoidingView>
        </View>
      </GestureHandlerRootView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalRoot: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
  },
  sheetContainer: {
    width: '100%',
    maxHeight: '92%',
  },
  sheet: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 12,
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  handle: {
    alignSelf: 'center',
    width: 44,
    height: 5,
    borderRadius: 999,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  content: {
    paddingBottom: 24,
  },
  themeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderWidth: 1,
    borderRadius: 12,
    gap: 12,
  },
  themeRowText: {
    flex: 1,
    gap: 2,
  },
  cancelButton: {
    marginTop: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
