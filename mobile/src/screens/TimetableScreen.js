import React, { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Banner, Card, Empty, Loading, PageTitle, Screen } from "../components";
import { ClassPlace } from "../components/ClassMode";
import { colors, space, type } from "../theme";
import { DAY_NAMES, DAY_SHORT, clock, todayIndex } from "../utils/format";
import { useResource } from "../useResource";

export default function TimetableScreen({ navigation }) {
  const { user } = useAuth();
  const canEdit = user.role === "lecturer" || user.role === "admin";
  const { data, error, loading, refreshing, refresh } = useResource("/timetable/");
  const [day, setDay] = useState(todayIndex());

  if (loading && !data) return <Loading />;

  const slots = (data || []).filter((slot) => slot.day === day);

  return (
    <Screen top onRefresh={refresh} refreshing={refreshing}>
      <PageTitle title="Timetable" subtitle="Classes for the units you are registered in this trimester" />
      <Banner message={error} />

      <View style={{ flexDirection: "row", marginBottom: space.lg }}>
        {DAY_SHORT.map((label, index) => {
          const selected = index === day;
          return (
            <Pressable
              key={label}
              onPress={() => setDay(index)}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              accessibilityLabel={DAY_NAMES[index]}
              style={{ flex: 1, alignItems: "center", paddingVertical: space.sm, borderBottomWidth: 2, borderBottomColor: selected ? colors.accent : colors.line }}
            >
              <Text style={{ fontSize: 13, fontWeight: selected ? "700" : "500", color: selected ? colors.ink : colors.muted }}>{label}</Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={[type.heading, { marginBottom: space.md }]}>{DAY_NAMES[day]}</Text>
      {slots.length === 0 ? (
        <Empty title="Nothing scheduled" message="No classes on this day." />
      ) : (
        slots.map((slot) => (
          <Card key={slot.id}>
            <Text style={type.label}>
              {clock(slot.start_time)} to {clock(slot.end_time)}
            </Text>
            <Text style={[type.heading, { marginTop: space.xs }]}>{slot.unit_title}</Text>
            <Text style={[type.small, { marginTop: space.xs }]}>{slot.unit_code}</Text>
            <ClassPlace slot={slot} onEdit={canEdit ? () => navigation.navigate("ClassLink", { slot }) : undefined} />
          </Card>
        ))
      )}
    </Screen>
  );
}
