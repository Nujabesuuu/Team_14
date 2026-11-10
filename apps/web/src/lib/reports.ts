import type { ReportContext, ReportReason, ReportStatus } from '@/api/types'

export const REPORT_REASONS: { value: ReportReason; label: string }[] = [
  { value: 'harassment', label: 'Harassment' },
  { value: 'inappropriate_photo', label: 'Bad photo' },
  { value: 'underage', label: 'Under 18' },
  { value: 'spam', label: 'Spam' },
  { value: 'other', label: 'Other' },
]

export const REASON_LABEL = Object.fromEntries(REPORT_REASONS.map((r) => [r.value, r.label])) as Record<
  ReportReason,
  string
>

export const CONTEXT_LABEL: Record<ReportContext, string> = { event: 'Event', chat: 'Chat', photo: 'Photo' }

/** How a report's state reads to the person who sent it and to the moderator. */
export const STATUS_LABEL: Record<ReportStatus, string> = {
  new: 'In review',
  dismissed: 'No action',
  warned: 'Warning issued',
  banned: 'Account blocked',
}

export const MAX_COMMENT = 500
