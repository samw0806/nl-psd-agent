// components/PreviewCanvas.tsx — PSD 预览画布 + 缩放
import { TransformWrapper, TransformComponent, useTransformContext } from 'react-zoom-pan-pinch'

interface Props {
  previewUrl: string | null
  previewVersion: number
}

function ScaleIndicator() {
  const { transformState } = useTransformContext()
  return (
    <div className="absolute bottom-12 left-4 text-xs text-[#666] bg-white/80 px-2 py-1 rounded z-10 pointer-events-none">
      缩放: {Math.round(transformState.scale * 100)}%
    </div>
  )
}

export function PreviewCanvas({ previewUrl, previewVersion }: Props) {
  const src = previewUrl
    ? `${previewUrl}${previewUrl.includes('?') ? '&' : '?'}v=${previewVersion}`
    : null

  return (
    <div className="flex-1 checkerboard overflow-hidden flex items-center justify-center relative">
      {src ? (
        <TransformWrapper
          initialScale={1}
          minScale={0.1}
          maxScale={10}
          centerOnInit
        >
          <ScaleIndicator />
          <TransformComponent
            wrapperClass="!w-full !h-full"
            contentClass="flex items-center justify-center"
          >
            <img
              src={src}
              alt="PSD 预览"
              className="max-w-none shadow-lg"
              style={{ display: 'block' }}
              draggable={false}
            />
          </TransformComponent>
        </TransformWrapper>
      ) : (
        <div className="flex flex-col items-center gap-3 text-[#999] select-none">
          <div className="text-4xl">□</div>
          <div className="text-sm">上传 PSD 文件后预览将显示在此处</div>
        </div>
      )}
    </div>
  )
}
