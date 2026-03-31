// components/ToolCallStatus.tsx — 工具调用状态展示
import { ToolCallEvent } from '../hooks/useSession'

interface Props {
  toolCalls: ToolCallEvent[]
}

const TOOL_LABELS: Record<string, string> = {
  get_psd_info: '读取图层信息',
  preview_psd: '生成预览图',
  set_visibility: '设置可见性',
  set_opacity: '设置不透明度',
  set_blend_mode: '设置混合模式',
  rename_layer: '重命名图层',
  reorder_layer: '重排图层',
  move_layer: '移动图层',
  remove_layer: '删除图层',
  add_layer: '添加图层',
  resample_layer: '缩放图层',
  create_group: '创建组',
  export_psd: '导出文件',
  read_text: '读取文字',
}

export function ToolCallStatus({ toolCalls }: Props) {
  if (toolCalls.length === 0) return null

  return (
    <div className="mt-2 flex flex-col gap-1">
      {toolCalls.map((tc, i) => (
        <div key={`${tc.tool_use_id ?? tc.tool}-${i}`} className="flex items-start gap-2 text-xs text-[#666]">
          <span className="mt-0.5">
            {tc.status === 'running' ? '⚙' : '✓'}
          </span>
          <span>
            {tc.status === 'running' ? (
              <>{TOOL_LABELS[tc.tool] ?? tc.tool}…</>
            ) : (
              <>{TOOL_LABELS[tc.tool] ?? tc.tool}</>
            )}
          </span>
        </div>
      ))}
    </div>
  )
}
