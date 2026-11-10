import React, { useMemo, useState } from "react";
import { Alert, Text, View } from "react-native";

import { api } from "../api";
import { Banner, Button, Card, Empty, Loading, Screen, Tag, TextField } from "../components";
import { colors, serif, space, type } from "../theme";
import { useResource } from "../useResource";

export default function RegisterUnitsScreen() {
  const { data, error, loading, refreshing, refresh, reload } = useResource("/units/");
  const [query, setQuery] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [problem, setProblem] = useState(null);

  const units = data || [];
  const mine = units.filter((unit) => unit.registered);
  const credits = mine.reduce((sum, unit) => sum + unit.credits, 0);

  const shown = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return units;
    return units.filter((unit) => `${unit.code} ${unit.title}`.toLowerCase().includes(needle));
  }, [units, query]);

  async function change(unit, register) {
    setBusyId(unit.id);
    setProblem(null);
    try {
      if (register) await api.post(`/units/${unit.id}/register/`);
      else await api.del(`/units/${unit.id}/register/`);
      await reload();
    } catch (e) {
      setProblem(e.message);
    } finally {
      setBusyId(null);
    }
  }

  function confirmDrop(unit) {
    Alert.alert("Drop unit", `Drop ${unit.code} ${unit.title} for this trimester?`, [
      { text: "Cancel", style: "cancel" },
      { text: "Drop", style: "destructive", onPress: () => change(unit, false) },
    ]);
  }

  if (loading && !data) return <Loading />;

  return (
    <Screen onRefresh={refresh} refreshing={refreshing}>
      <Card style={{ flexDirection: "row", gap: space.lg, borderLeftWidth: 3, borderLeftColor: colors.accent }}>
        <View style={{ flex: 1 }}>
          <Text style={{ fontFamily: serif, fontSize: 30, color: colors.ink }}>{mine.length}</Text>
          <Text style={type.small}>Units registered</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontFamily: serif, fontSize: 30, color: colors.ink }}>{credits}</Text>
          <Text style={type.small}>Credits</Text>
        </View>
      </Card>
      <Text style={[type.small, { marginBottom: space.lg }]}>
        Registrations you make here are for the current trimester. Units you register for on the KCA portal appear here too.
      </Text>

      <Banner message={problem || error} />
      <TextField label="Search units" value={query} onChangeText={setQuery} placeholder="Code or title" autoCorrect={false} style={{ marginBottom: space.md }} />

      {shown.length === 0 ? <Empty title="No units found" message={units.length ? "Try a different search." : "No units have been added yet."} /> : null}
      {shown.map((unit) => (
        <Card key={unit.id}>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
            <Text style={type.label}>{unit.code}</Text>
            <View style={{ flexDirection: "row", gap: space.sm }}>
              {unit.registered ? <Tag tone="accent">Registered</Tag> : null}
              <Tag>{unit.credits} credits</Tag>
            </View>
          </View>
          <Text style={[type.heading, { marginTop: space.sm }]}>{unit.title}</Text>
          {unit.lecturer_name ? <Text style={[type.small, { marginTop: space.xs }]}>{unit.lecturer_name}</Text> : null}
          <Button
            title={unit.registered ? "Drop" : "Register"}
            variant={unit.registered ? "secondary" : "primary"}
            loading={busyId === unit.id}
            disabled={busyId !== null && busyId !== unit.id}
            onPress={() => (unit.registered ? confirmDrop(unit) : change(unit, true))}
            style={{ marginTop: space.md, minHeight: 44 }}
          />
        </Card>
      ))}
    </Screen>
  );
}
