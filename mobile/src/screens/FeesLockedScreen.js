import React, { useState } from "react";
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from "react-native";
import { useAuth } from "../auth/AuthContext";
import { colors } from "../theme";

// Shown instead of the whole campus when a student's fees are outstanding.
export default function FeesLockedScreen() {
  const { signOut, refreshUser } = useAuth();
  const [checking, setChecking] = useState(false);

  const check = async () => {
    setChecking(true);
    try { await refreshUser(); } catch (e) { /* offline: stay locked, the button can be pressed again */ } finally { setChecking(false); }
  };

  return (
    <View style={s.wrap}>
      <Text style={s.title}>Fees outstanding</Text>
      <Text style={s.body}>
        The virtual campus, exam card and exam timetable are available once your school fees are cleared.
        Please settle your balance with the finance office. It can take a short while to reflect here.
      </Text>
      <TouchableOpacity style={s.primary} onPress={check} disabled={checking}>
        {checking ? <ActivityIndicator color={colors.primaryText} /> : <Text style={s.primaryText}>Check again</Text>}
      </TouchableOpacity>
      <TouchableOpacity style={s.secondary} onPress={signOut}>
        <Text style={s.secondaryText}>Sign out</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: colors.surface },
  title: { fontSize: 24, fontWeight: "700", marginBottom: 12 },
  body: { fontSize: 16, lineHeight: 23, color: colors.inkSoft, marginBottom: 28 },
  primary: { backgroundColor: colors.primary, padding: 14, borderRadius: 10, alignItems: "center", marginBottom: 12 },
  primaryText: { color: colors.primaryText, fontWeight: "600", fontSize: 16 },
  secondary: { padding: 14, alignItems: "center" },
  secondaryText: { color: colors.primary, fontSize: 16 },
});
