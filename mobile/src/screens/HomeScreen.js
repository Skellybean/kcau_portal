import React from "react";
import { Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Banner, Card, Loading, Screen, SectionLabel, Tag } from "../components";
import { ClassPlace } from "../components/ClassMode";
import { colors, serif, space, type } from "../theme";
import { clock, firstName, longDate, roleLabel, shortDate } from "../utils/format";
import { useResource } from "../useResource";

function Figure({ value, label }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={{ fontFamily: serif, fontSize: 30, color: colors.ink }}>{value}</Text>
      <Text style={type.small}>{label}</Text>
    </View>
  );
}

export default function HomeScreen({ navigation }) {
  const { user } = useAuth();
  const { data, error, loading, refreshing, refresh } = useResource("/dashboard/");

  if (loading && !data) return <Loading />;

  return (
    <Screen top onRefresh={refresh} refreshing={refreshing}>
      <Text style={type.label}>{longDate()}</Text>
      <Text style={[type.display, { marginTop: space.xs }]}>Hello, {firstName(user.full_name)}</Text>
      <Text style={[type.small, { marginTop: space.xs, marginBottom: space.lg }]}>
        {roleLabel(user.role)}
        {user.programme ? `, ${user.programme}` : ""}
      </Text>

      <Banner message={error} />

      {data ? (
        <>
          <Card style={{ flexDirection: "row", gap: space.lg }}>
            <Figure value={data.unit_count} label={user.role === "lecturer" ? "Units you teach" : "Units this trimester"} />
            {user.role === "student" ? (
              <Figure value={data.average_mark != null ? data.average_mark : "-"} label="Average mark" />
            ) : null}
          </Card>

          <SectionLabel>Next class</SectionLabel>
          {data.next_class ? (
            <Card style={{ borderLeftWidth: 3, borderLeftColor: colors.accent }}>
              <Text style={type.heading}>{data.next_class.unit_title}</Text>
              <Text style={[type.small, { marginTop: space.xs }]}>
                {data.next_class.unit_code}  |  {clock(data.next_class.start_time)} to {clock(data.next_class.end_time)}
              </Text>
              <ClassPlace slot={data.next_class} />
            </Card>
          ) : (
            <Card>
              <Text style={type.body}>No more classes today.</Text>
            </Card>
          )}

          {data.today.length > 1 || (data.today.length === 1 && !data.next_class) ? (
            <>
              <SectionLabel>Today</SectionLabel>
              <Card>
                {data.today.map((slot, index) => (
                  <View
                    key={slot.id}
                    style={{ flexDirection: "row", paddingVertical: space.sm, borderTopWidth: index ? 1 : 0, borderTopColor: colors.line }}
                  >
                    <Text style={[type.small, { width: 96 }]}>
                      {clock(slot.start_time)} - {clock(slot.end_time)}
                    </Text>
                    <View style={{ flex: 1 }}>
                      <Text style={type.body}>{slot.unit_title}</Text>
                      <Text style={type.small}>{slot.mode === "in_person" ? slot.venue : slot.mode === "online" ? "Online" : `Hybrid, ${slot.venue}`}</Text>
                    </View>
                  </View>
                ))}
              </Card>
            </>
          ) : null}

          <SectionLabel>Latest notices</SectionLabel>
          {data.announcements.length === 0 ? (
            <Card>
              <Text style={type.body}>No notices yet.</Text>
            </Card>
          ) : (
            data.announcements.map((item) => (
              <Card key={item.id} onPress={() => navigation.navigate("Notices")} accessibilityLabel={`Notice: ${item.title}`}>
                {item.pinned ? <Tag tone="accent">Pinned</Tag> : null}
                <Text style={[type.heading, { marginTop: item.pinned ? space.sm : 0 }]}>{item.title}</Text>
                <Text style={[type.small, { marginTop: space.xs }]} numberOfLines={2}>
                  {item.body}
                </Text>
                <Text style={[type.small, { marginTop: space.sm, color: colors.muted }]}>{shortDate(item.created_at)}</Text>
              </Card>
            ))
          )}
        </>
      ) : null}
    </Screen>
  );
}
