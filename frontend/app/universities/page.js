"use client";

import AttendeePageLayout from "../../components/AttendeePageLayout";
import AttendeeUniversitiesView from "../../components/AttendeeUniversitiesView";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Universities() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Universities & Programs" attendee={attendee} showLoadMore>
      {attendee.data && <AttendeeUniversitiesView universities={attendee.data.universities} />}
    </AttendeePageLayout>
  );
}
