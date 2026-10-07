"use client";

import AttendeeEmployersView from "../../components/AttendeeEmployersView";
import AttendeePageLayout from "../../components/AttendeePageLayout";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Employers() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Participating Employers" attendee={attendee}>
      {attendee.data && <AttendeeEmployersView employers={attendee.data.employers} />}
    </AttendeePageLayout>
  );
}
