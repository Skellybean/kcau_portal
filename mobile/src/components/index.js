import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors, radius, space, type } from "../theme";

export function Screen({ children, onRefresh, refreshing = false, top = false, keyboard = false, contentStyle }) {
  const insets = useSafeAreaInsets();
  const body = (
    <ScrollView
      style={{ backgroundColor: colors.paper }}
      contentContainerStyle={[
        { padding: space.lg, paddingTop: (top ? insets.top : 0) + space.lg, paddingBottom: space.xxl + insets.bottom },
        contentStyle,
      ]}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        onRefresh ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} colors={[colors.primary]} /> : undefined
      }
    >
      {children}
    </ScrollView>
  );
  if (!keyboard) return <View style={styles.fill}>{body}</View>;
  return (
    <KeyboardAvoidingView style={styles.fill} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      {body}
    </KeyboardAvoidingView>
  );
}

export function PageTitle({ title, subtitle }) {
  return (
    <View style={{ marginBottom: space.xl }}>
      <Text style={type.display} accessibilityRole="header">
        {title}
      </Text>
      {subtitle ? <Text style={[type.small, { marginTop: space.xs }]}>{subtitle}</Text> : null}
    </View>
  );
}

export function SectionLabel({ children, style }) {
  return <Text style={[type.label, { marginBottom: space.sm, marginTop: space.lg }, style]}>{children}</Text>;
}

export function Card({ children, style, onPress, accessibilityLabel }) {
  const content = <View style={[styles.card, style]}>{children}</View>;
  if (!onPress) return content;
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={accessibilityLabel} style={({ pressed }) => pressed && { opacity: 0.7 }}>
      {content}
    </Pressable>
  );
}

export function Button({ title, onPress, variant = "primary", loading = false, disabled = false, style }) {
  const inactive = disabled || loading;
  const palette = {
    primary: { bg: colors.primary, fg: colors.primaryText, border: colors.primary },
    secondary: { bg: "transparent", fg: colors.primary, border: colors.primary },
    quiet: { bg: "transparent", fg: colors.primary, border: "transparent" },
    danger: { bg: "transparent", fg: colors.danger, border: colors.danger },
  }[variant];
  return (
    <Pressable
      onPress={inactive ? undefined : onPress}
      accessibilityRole="button"
      accessibilityState={{ disabled: inactive, busy: loading }}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: palette.bg, borderColor: palette.border, opacity: inactive ? 0.55 : pressed ? 0.8 : 1 },
        style,
      ]}
    >
      {loading ? <ActivityIndicator color={palette.fg} /> : <Text style={[styles.buttonText, { color: palette.fg }]}>{title}</Text>}
    </Pressable>
  );
}

export function TextField({ label, error, hint, secure = false, style, ...props }) {
  const [hidden, setHidden] = useState(secure);
  const [focused, setFocused] = useState(false);
  return (
    <View style={[{ marginBottom: space.lg }, style]}>
      <Text style={[type.label, { marginBottom: space.xs }]}>{label}</Text>
      <View
        style={[
          styles.inputWrap,
          props.multiline && { alignItems: "flex-start" },
          focused && { borderColor: colors.primary },
          error && { borderColor: colors.danger },
        ]}
      >
        <TextInput
          {...props}
          secureTextEntry={hidden}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholderTextColor={colors.muted}
          accessibilityLabel={label}
          style={[styles.input, props.multiline && { minHeight: 140, paddingTop: 12 }]}
        />
        {secure ? (
          <Pressable onPress={() => setHidden((h) => !h)} accessibilityRole="button" accessibilityLabel={hidden ? "Show password" : "Hide password"} hitSlop={8}>
            <Text style={styles.toggle}>{hidden ? "Show" : "Hide"}</Text>
          </Pressable>
        ) : null}
      </View>
      {error ? <Text style={styles.fieldError}>{error}</Text> : hint ? <Text style={[type.small, { marginTop: space.xs }]}>{hint}</Text> : null}
    </View>
  );
}

export function Banner({ message, tone = "error", style }) {
  if (!message) return null;
  const isError = tone === "error";
  return (
    <View
      accessibilityLiveRegion="polite"
      style={[
        styles.banner,
        { backgroundColor: isError ? colors.dangerSoft : colors.accentSoft, borderLeftColor: isError ? colors.danger : colors.accent },
        style,
      ]}
    >
      <Text style={[type.body, { color: isError ? colors.danger : colors.ink }]}>{message}</Text>
    </View>
  );
}

export function Loading() {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={colors.primary} />
    </View>
  );
}

export function Empty({ title, message }) {
  return (
    <View style={styles.empty}>
      <Text style={type.heading}>{title}</Text>
      {message ? <Text style={[type.small, { marginTop: space.xs, textAlign: "center" }]}>{message}</Text> : null}
    </View>
  );
}

export function Tag({ children, tone = "neutral" }) {
  const accent = tone === "accent";
  return (
    <View style={[styles.tag, accent && { backgroundColor: colors.accentSoft, borderColor: colors.accent }]}>
      <Text style={[styles.tagText, accent && { color: colors.accent }]}>{children}</Text>
    </View>
  );
}

export function Chip({ label, selected, onPress }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      style={[styles.chip, selected && { backgroundColor: colors.primary, borderColor: colors.primary }]}
    >
      <Text style={[styles.chipText, selected && { color: colors.primaryText }]}>{label}</Text>
    </Pressable>
  );
}

export function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={type.small}>{label}</Text>
      <Text style={[type.body, { flexShrink: 1, textAlign: "right" }]}>{value || "Not set"}</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  fill: { flex: 1, backgroundColor: colors.paper },
  card: {
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: space.lg,
    marginBottom: space.md,
  },
  button: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.sm,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  buttonText: { fontSize: 15, fontWeight: "600", letterSpacing: 0.3 },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.sm,
    paddingHorizontal: space.md,
  },
  input: { flex: 1, minHeight: 48, fontSize: 16, color: colors.ink },
  toggle: { color: colors.primary, fontWeight: "600", fontSize: 13, paddingLeft: space.md },
  fieldError: { color: colors.danger, fontSize: 13, marginTop: space.xs },
  banner: { borderLeftWidth: 3, borderRadius: radius.sm, padding: space.md, marginBottom: space.lg },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: space.xxl },
  empty: { alignItems: "center", paddingVertical: space.xxl, paddingHorizontal: space.lg },
  tag: { alignSelf: "flex-start", borderWidth: 1, borderColor: colors.line, borderRadius: radius.sm, paddingHorizontal: 8, paddingVertical: 2 },
  tagText: { fontSize: 11, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase", color: colors.inkSoft },
  chip: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.surface, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8, marginRight: space.sm },
  chipText: { fontSize: 13, color: colors.ink, fontWeight: "500" },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", paddingVertical: space.md, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.line, gap: space.lg },
});
