"use client";

import AttendeePageLayout from "../../../components/AttendeePageLayout";
import AttendeeSessionsView from "../../../components/AttendeeSessionsView";
import useAttendeeData from "../../../hooks/useAttendeeData";

export default function Sessions() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Event Sessions" attendee={attendee}>
      {attendee.data && <AttendeeSessionsView sessions={attendee.data.sessions} me={attendee.me} busy={attendee.busy} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
