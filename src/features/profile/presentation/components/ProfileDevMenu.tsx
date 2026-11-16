import { useEffect } from 'react';
import {
  Dimensions,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
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

const AnimatedScrollView = Animated.createAnimatedComponent(ScrollView);

import { theme } from '@/core/theme/theme';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from './ProfileForm';

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
  const translateY = useSharedValue(0);
  const scrollY = useSharedValue(0);
  const sheetHeight = useSharedValue(SCREEN_HEIGHT);

  useEffect(() => {
    if (visible) {
      translateY.value = 0;
      scrollY.value = 0;
    }
  }, [scrollY, translateY, visible]);

  const closeSheet = () => {
    onClose();
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
                style={[styles.sheet, sheetAnimatedStyle]}
                onLayout={(event) => {
                  sheetHeight.value = event.nativeEvent.layout.height;
                }}
              >
                <View style={styles.handle} />
                <Text style={styles.title}>Editar perfil</Text>

                <AnimatedScrollView
                  contentContainerStyle={styles.content}
                  keyboardShouldPersistTaps="handled"
                  showsVerticalScrollIndicator={false}
                  onScroll={handleScroll}
                  scrollEventThrottle={16}
                  bounces={false}
                >
                  <ProfileForm
                    initialProfile={initialProfile}
                    submitLabel="Guardar"
                    onSubmit={onSubmit}
                    // variant="dark"
                    variant="light"
                  />

                  <Pressable style={styles.cancelButton} onPress={onClose} accessibilityRole="button">
                    <Text style={styles.cancelButtonText}>Cancelar</Text>
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
    // backgroundColor: '#0B0F1A',
    backgroundColor: theme.colors.surface,
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
    // backgroundColor: '#374151',
    backgroundColor: theme.colors.border,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    // color: '#F9FAFB',
    color: theme.colors.text,
    marginBottom: 4,
  },
  content: {
    paddingBottom: 24,
  },
  cancelButton: {
    marginTop: 8,
    paddingVertical: 14,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 14,
    fontWeight: '500',
    // color: '#9CA3AF',
    color: theme.colors.textSecondary,
  },
});
