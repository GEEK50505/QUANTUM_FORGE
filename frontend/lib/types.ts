import { z } from 'zod'

export const JobSchema = z.object({
  id: z.string().uuid(),
  job_key: z.string(),
  user_id: z.string().uuid().nullable(),
  status: z.enum(['queued', 'running', 'completed', 'failed']),
  payload: z.record(z.any()).nullable(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export type Job = z.infer<typeof JobSchema>

export const JobPayloadSchema = z.object({
  job_key: z.string(),
  xyz_file: z.string().optional(),
  xyz_inline: z.string().optional(),
  sdf_inline: z.string().optional(),
  optimization_level: z.enum(['normal', 'tight']).default('normal'),
})

export type JobPayload = z.infer<typeof JobPayloadSchema>
