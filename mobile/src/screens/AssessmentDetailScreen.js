import React, { useCallback, useEffect, useState } from "react";
import { ScrollView, View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator, StyleSheet } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import api from "../api";
import { dateTime } from "../utils/dates";

export default function AssessmentDetailScreen({ route }) {
  const { id } = route.params;
  const [a, setA] = useState(null);
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await api.get(`/assessments/${id}/`);
      setA(data);
      setText(data.my_submission?.text_answer || "");
    } catch (e) {
      setError(e.message || "Could not load this item.");
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const pick = async () => {
    const res = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
    if (res.canceled) return;
    const f = res.assets[0];
    setFile({ uri: f.uri, name: f.name, type: f.mimeType || "application/octet-stream" });
  };

  const send = async () => {
    setError("");
    const form = new FormData();
    if (text.trim()) form.append("text_answer", text.trim());
    if (file) form.append("file", file);
    setBusy(true);
    try {
      const updated = await api.postForm(`/assessments/${id}/submit/`, form);
      setA(updated);
      setFile(null);
      Alert.alert("Submitted", "Your work has been received.");
    } catch (e) {
      setError(e.message || "Submission failed.");
    } finally {
      setBusy(false);
    }
  };

  const confirm = () => {
    if (!text.trim() && !file) { setError("Add an answer or attach a file."); return; }
    Alert.alert("Submit work?", a.my_submission ? "This replaces your earlier submission." : "You can resubmit until the deadline.", [
      { text: "Cancel", style: "cancel" },
      { text: "Submit", onPress: send },
    ]);
  };

  if (!a) return <View style={s.center}>{error ? <Text>{error}</Text> : <ActivityIndicator />}</View>;
  const mine = a.my_submission;
  const marked = mine && mine.marks != null;
  const canEdit = a.accepting && !marked;

  return (
    <ScrollView style={s.wrap} contentContainerStyle={{ padding: 16 }} keyboardShouldPersistTaps="handled">
      <Text style={s.kind}>{a.kind_label} · {a.unit_code} {a.unit_title}</Text>
      <Text style={s.title}>{a.title}</Text>
      <Text style={s.meta}>Due {dateTime(a.due_at)} · {a.max_marks} marks</Text>
      {!!a.instructions && <Text style={s.body}>{a.instructions}</Text>}

      {marked && (
        <View style={s.marked}>
          <Text style={s.markedTitle}>Marks: {mine.marks} / {a.max_marks}</Text>
          {!!mine.feedback && <Text>{mine.feedback}</Text>}
        </View>
      )}
      {mine && !marked && <Text style={s.info}>Submitted {dateTime(mine.submitted_at)}{mine.file_name ? ` · ${mine.file_name}` : ""}</Text>}

      {canEdit ? (
        <>
          {a.allow_text && (
            <TextInput style={s.input} multiline placeholder="Type your answer" value={text} onChangeText={setText} textAlignVertical="top" />
          )}
          {a.allow_file && (
            <TouchableOpacity style={s.attach} onPress={pick}>
              <Text style={s.attachText}>{file ? file.name : "Attach a file (max 5 MB)"}</Text>
            </TouchableOpacity>
          )}
          {!!error && <Text style={s.error}>{error}</Text>}
          <TouchableOpacity style={s.submit} onPress={confirm} disabled={busy}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={s.submitText}>{mine ? "Resubmit" : "Submit"}</Text>}
          </TouchableOpacity>
        </>
      ) : (
        !marked && <Text style={s.info}>{mine ? "" : "This work is closed."}</Text>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f4f6f9" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  kind: { color: "#1a4d8f", fontWeight: "600" },
  title: { fontSize: 22, fontWeight: "700", marginTop: 4 },
  meta: { color: "#666", marginTop: 4 },
  body: { marginTop: 14, fontSize: 16, lineHeight: 22 },
  info: { marginTop: 14, color: "#555" },
  marked: { backgroundColor: "#e3f6e8", padding: 12, borderRadius: 8, marginTop: 14 },
  markedTitle: { fontWeight: "700", marginBottom: 4 },
  input: { backgroundColor: "#fff", borderRadius: 8, minHeight: 140, padding: 12, marginTop: 16, fontSize: 16 },
  attach: { backgroundColor: "#fff", borderRadius: 8, padding: 14, marginTop: 12, borderWidth: 1, borderColor: "#cdd6e4", borderStyle: "dashed" },
  attachText: { color: "#1a4d8f" },
  error: { color: "#b00020", marginTop: 10 },
  submit: { backgroundColor: "#1a4d8f", padding: 14, borderRadius: 10, alignItems: "center", marginTop: 16 },
  submitText: { color: "#fff", fontWeight: "600", fontSize: 16 },
});
