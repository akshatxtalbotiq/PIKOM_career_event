"use client";

import AttendeePageLayout from "../../components/AttendeePageLayout";
import AttendeeInterviewsView from "../../components/AttendeeInterviewsView";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Interviews() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Interview Availability" attendee={attendee}>
      {attendee.data && <AttendeeInterviewsView slots={attendee.data.interview_slots} me={attendee.me} busy={attendee.busy} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
