"use client";

import AttendeePageLayout from "../../components/AttendeePageLayout";
import AttendeeSessionsView from "../../components/AttendeeSessionsView";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Sessions() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Keynotes & Sessions" attendee={attendee} showLoadMore>
      {attendee.data && <AttendeeSessionsView sessions={attendee.data.sessions} schedule={attendee.schedule} me={attendee.me} busy={attendee.busy} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
