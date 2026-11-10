import React from "react";
import { Text } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Card, Row, Screen, SectionLabel, Tag } from "../components";
import { ClassPlace } from "../components/ClassMode";
import { space, type } from "../theme";
import { DAY_NAMES, clock } from "../utils/format";
import { useResource } from "../useResource";

export default function UnitDetailScreen({ route, navigation }) {
  const { user } = useAuth();
  const canEdit = user.role === "lecturer" || user.role === "admin";
  const { unit } = route.params;
  const { data } = useResource("/timetable/");
  const slots = (data || []).filter((slot) => slot.unit === unit.id);

  return (
    <Screen>
      <Text style={type.label}>{unit.code}</Text>
      <Text style={[type.title, { marginTop: space.xs, marginBottom: space.md }]}>{unit.title}</Text>
      {unit.registered ? <Tag tone="accent">Registered this trimester</Tag> : null}
      {unit.description ? <Text style={[type.body, { marginTop: space.lg }]}>{unit.description}</Text> : null}

      <SectionLabel>Details</SectionLabel>
      <Card style={{ paddingVertical: 0 }}>
        <Row label="Credits" value={String(unit.credits)} />
        <Row label="Lecturer" value={unit.lecturer_name} />
      </Card>

      <SectionLabel>Weekly classes</SectionLabel>
      {slots.length === 0 ? (
        <Text style={type.small}>No classes scheduled yet.</Text>
      ) : (
        slots.map((slot) => (
          <Card key={slot.id}>
            <Text style={type.heading}>{DAY_NAMES[slot.day]}</Text>
            <Text style={[type.small, { marginTop: space.xs }]}>
              {clock(slot.start_time)} to {clock(slot.end_time)}
            </Text>
            <ClassPlace slot={slot} onEdit={canEdit ? () => navigation.navigate("ClassLink", { slot }) : undefined} />
          </Card>
        ))
      )}
    </Screen>
  );
}
