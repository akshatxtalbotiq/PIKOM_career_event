"use client";

import AttendeeJobsView from "../../components/AttendeeJobsView";
import AttendeePageLayout from "../../components/AttendeePageLayout";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Jobs() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Jobs & Opportunities" attendee={attendee} showLoadMore>
      {attendee.data && <AttendeeJobsView jobs={attendee.data.jobs} me={attendee.me} busy={attendee.busy} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
