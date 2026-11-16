import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { theme } from '@/core/theme/theme';

import type { UserProfile } from '../../domain/entities/UserProfile';
import { ProfileForm } from './ProfileForm';

interface ProfileDevMenuProps {
  visible: boolean;
  initialProfile: UserProfile;
  onSubmit: (profile: UserProfile) => Promise<void> | void;
  onClose: () => void;
}

export function ProfileDevMenu({ visible, initialProfile, onSubmit, onClose }: ProfileDevMenuProps) {
  return (
    <Modal transparent visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <Pressable style={styles.backdrop} onPress={onClose} accessibilityRole="button" />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.sheetContainer}
        >
          <View style={styles.sheet}>
            <View style={styles.handle} />
            <Text style={styles.title}>Editar perfil</Text>

            <ScrollView
              contentContainerStyle={styles.content}
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
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
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
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
