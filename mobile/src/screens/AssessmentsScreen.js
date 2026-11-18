import React, { useCallback, useState } from "react";
import { View, Text, FlatList, TouchableOpacity, RefreshControl, StyleSheet } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import api from "../api";
import { dateTime } from "../utils/dates";
import { colors } from "../theme";

function status(a) {
  const m = a.my_submission;
  if (m && m.marks != null) return "Marked";
  if (m) return "Submitted";
  return a.accepting ? "Open" : "Closed";
}

export default function AssessmentsScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get("/assessments/");
      setItems(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      setError(e.message || "Could not load assignments.");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <FlatList
      style={s.list}
      data={items}
      keyExtractor={(a) => String(a.id)}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={!loading && <Text style={s.empty}>{error || "No assignments or CATs yet."}</Text>}
      renderItem={({ item }) => {
        const st = status(item);
        return (
          <TouchableOpacity style={s.card} onPress={() => navigation.navigate("AssessmentDetail", { id: item.id })}>
            <Text style={s.kind}>{item.kind_label} · {item.unit_code}</Text>
            <Text style={s.title}>{item.title}</Text>
            <Text style={s.meta}>Due {dateTime(item.due_at)}</Text>
            <Text style={[s.tag, st === "Open" && s.open, st === "Closed" && s.closed]}>{st}</Text>
          </TouchableOpacity>
        );
      }}
    />
  );
}

const s = StyleSheet.create({
  list: { flex: 1, backgroundColor: colors.paper },
  empty: { textAlign: "center", marginTop: 40, color: colors.inkSoft, paddingHorizontal: 24 },
  card: { backgroundColor: colors.surface, margin: 12, marginBottom: 0, padding: 14, borderRadius: 10 },
  kind: { color: colors.primary, fontWeight: "600", fontSize: 12 },
  title: { fontSize: 17, fontWeight: "600", marginTop: 4 },
  meta: { color: colors.inkSoft, marginTop: 4 },
  tag: { alignSelf: "flex-start", marginTop: 8, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, backgroundColor: colors.accentSoft, color: colors.primary, fontSize: 12, overflow: "hidden" },
  open: { backgroundColor: colors.successSoft, color: colors.success },
  closed: { backgroundColor: colors.line, color: colors.inkSoft },
});
