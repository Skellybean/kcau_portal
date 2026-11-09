import React from "react";
import { Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Banner, Card, Empty, Loading, Screen, SectionLabel } from "../components";
import { colors, serif, space, type } from "../theme";
import { useResource } from "../useResource";

function Mark({ label, value }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={type.label}>{label}</Text>
      <Text style={[type.body, { marginTop: 2 }]}>{value}</Text>
    </View>
  );
}

export default function ResultsScreen() {
  const { user } = useAuth();
  const { data, error, loading, refreshing, refresh } = useResource("/results/");
  const isStudent = user.role === "student";

  if (loading && !data) return <Loading />;

  const rows = data || [];
  const credits = rows.reduce((sum, r) => sum + r.credits, 0);
  const weighted = rows.reduce((sum, r) => sum + Number(r.total) * r.credits, 0);
  const average = credits ? (weighted / credits).toFixed(1) : null;

  const byYear = rows.reduce((groups, row) => {
    (groups[row.academic_year] = groups[row.academic_year] || []).push(row);
    return groups;
  }, {});

  return (
    <Screen onRefresh={refresh} refreshing={refreshing}>
      <Text style={[type.small, { marginBottom: space.lg }]}>
        Sample results for demonstration. CAT is marked out of 30 and the exam out of 70.
      </Text>
      <Banner message={error} />

      {isStudent && average ? (
        <Card style={{ borderLeftWidth: 3, borderLeftColor: colors.accent }}>
          <Text style={type.label}>Credit-weighted average</Text>
          <Text style={{ fontFamily: serif, fontSize: 36, color: colors.ink, marginTop: space.xs }}>{average}</Text>
        </Card>
      ) : null}

      {rows.length === 0 ? <Empty title="No results yet" message="Results will appear here once they are released." /> : null}

      {Object.keys(byYear).map((year) => (
        <View key={year}>
          <SectionLabel>{year}</SectionLabel>
          {byYear[year].map((row) => (
            <Card key={row.id}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: space.md }}>
                  <Text style={type.label}>{row.unit_code}</Text>
                  <Text style={[type.heading, { marginTop: 2 }]}>{row.unit_title}</Text>
                  {!isStudent ? <Text style={[type.small, { marginTop: space.xs }]}>{row.student_name}</Text> : null}
                </View>
                <Text style={{ fontFamily: serif, fontSize: 32, color: colors.primary }} accessibilityLabel={`Grade ${row.grade}`}>
                  {row.grade}
                </Text>
              </View>
              <View style={{ flexDirection: "row", marginTop: space.md, paddingTop: space.md, borderTopWidth: 1, borderTopColor: colors.line }}>
                <Mark label="CAT" value={`${Number(row.cat_mark)} / 30`} />
                <Mark label="Exam" value={`${Number(row.exam_mark)} / 70`} />
                <Mark label="Total" value={`${Number(row.total)} / 100`} />
              </View>
            </Card>
          ))}
        </View>
      ))}
    </Screen>
  );
}
