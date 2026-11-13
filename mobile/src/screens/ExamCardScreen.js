import React, { useCallback, useState } from "react";
import { ScrollView, View, Text, StyleSheet } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import api from "../api";
import { examDate, shortTime } from "../utils/dates";

export default function ExamCardScreen() {
  const [card, setCard] = useState(null);
  const [error, setError] = useState("");

  useFocusEffect(useCallback(() => {
    api.get("/exam-card/").then(setCard).catch((e) => setError(e.message || "Could not load your exam card."));
  }, []));

  if (!card) return <View style={s.center}><Text>{error || "Loading…"}</Text></View>;
  const st = card.student;

  return (
    <ScrollView style={s.wrap} contentContainerStyle={{ padding: 16 }}>
      <View style={s.card}>
        <Text style={s.heading}>Examination card</Text>
        <Text style={s.trim}>{card.trimester}</Text>
        <Text style={s.name}>{st.full_name}</Text>
        {!!st.admission_number && <Text style={s.meta}>Adm. no: {st.admission_number}</Text>}
        {!!st.programme && <Text style={s.meta}>{st.programme}</Text>}
        <Text style={s.meta}>{st.email}</Text>
        <View style={s.rule} />
        {card.units.length === 0 && <Text style={s.meta}>No registered units this trimester.</Text>}
        {card.units.map((u) => (
          <View key={u.code} style={s.unit}>
            <Text style={s.unitTitle}>{u.code} {u.title}</Text>
            {u.exams.length === 0
              ? <Text style={s.meta}>Exam date not yet set</Text>
              : u.exams.map((e, i) => (
                  <Text key={i} style={s.meta}>{examDate(e.date)} · {shortTime(e.start_time)}–{shortTime(e.end_time)} · {e.venue}</Text>
                ))}
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f4f6f9" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  card: { backgroundColor: "#fff", borderRadius: 12, padding: 18, borderWidth: 2, borderColor: "#1a4d8f" },
  heading: { fontSize: 20, fontWeight: "800", color: "#1a4d8f", textAlign: "center" },
  trim: { textAlign: "center", color: "#666", marginBottom: 14 },
  name: { fontSize: 18, fontWeight: "700" },
  meta: { color: "#444", marginTop: 3 },
  rule: { height: 1, backgroundColor: "#dde3ee", marginVertical: 14 },
  unit: { marginBottom: 12 },
  unitTitle: { fontWeight: "600", fontSize: 15 },
});
