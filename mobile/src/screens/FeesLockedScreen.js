import React, { useState } from "react";
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from "react-native";
import { useAuth } from "../auth/AuthContext";

// Shown instead of the whole campus when a student's fees are outstanding.
// Expects useAuth() to provide { user, logout, refreshUser }.
export default function FeesLockedScreen() {
  const { logout, refreshUser } = useAuth();
  const [checking, setChecking] = useState(false);

  const check = async () => {
    setChecking(true);
    try { await refreshUser(); } finally { setChecking(false); }
  };

  return (
    <View style={s.wrap}>
      <Text style={s.title}>Fees outstanding</Text>
      <Text style={s.body}>
        The virtual campus, exam card and exam timetable are available once your school fees are cleared.
        Please settle your balance with the finance office. It can take a short while to reflect here.
      </Text>
      <TouchableOpacity style={s.primary} onPress={check} disabled={checking}>
        {checking ? <ActivityIndicator color="#fff" /> : <Text style={s.primaryText}>Check again</Text>}
      </TouchableOpacity>
      <TouchableOpacity style={s.secondary} onPress={logout}>
        <Text style={s.secondaryText}>Sign out</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#fff" },
  title: { fontSize: 24, fontWeight: "700", marginBottom: 12 },
  body: { fontSize: 16, lineHeight: 23, color: "#444", marginBottom: 28 },
  primary: { backgroundColor: "#1a4d8f", padding: 14, borderRadius: 10, alignItems: "center", marginBottom: 12 },
  primaryText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  secondary: { padding: 14, alignItems: "center" },
  secondaryText: { color: "#1a4d8f", fontSize: 16 },
});
