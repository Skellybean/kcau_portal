import React, { useCallback, useState } from "react";
import { SectionList, Text, View, RefreshControl, StyleSheet } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import api from "../api";
import { examDate, shortTime } from "../utils/dates";

export default function ExamTimetableScreen() {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get("/exams/");
      const rows = Array.isArray(data) ? data : data.results || [];
      const byDate = {};
      rows.forEach((r) => { (byDate[r.date] = byDate[r.date] || []).push(r); });
      setSections(Object.keys(byDate).sort().map((d) => ({ title: examDate(d), data: byDate[d] })));
    } catch (e) {
      setError(e.message || "Could not load the exam timetable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <SectionList
      style={s.list}
      sections={sections}
      keyExtractor={(r) => String(r.id)}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={!loading && <Text style={s.empty}>{error || "No exams scheduled yet."}</Text>}
      renderSectionHeader={({ section }) => <Text style={s.header}>{section.title}</Text>}
      renderItem={({ item }) => (
        <View style={s.card}>
          <Text style={s.unit}>{item.unit_code} {item.unit_title}</Text>
          <Text style={s.meta}>{shortTime(item.start_time)} – {shortTime(item.end_time)} · {item.venue}</Text>
        </View>
      )}
    />
  );
}

const s = StyleSheet.create({
  list: { flex: 1, backgroundColor: "#f4f6f9" },
  empty: { textAlign: "center", marginTop: 40, color: "#666", paddingHorizontal: 24 },
  header: { padding: 12, paddingTop: 18, fontWeight: "700", color: "#1a4d8f" },
  card: { backgroundColor: "#fff", marginHorizontal: 12, marginBottom: 8, padding: 14, borderRadius: 10 },
  unit: { fontSize: 16, fontWeight: "600" },
  meta: { color: "#666", marginTop: 4 },
});
