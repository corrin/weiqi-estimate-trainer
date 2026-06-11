import { useEffect, useRef } from 'react'
import { createBoard, STONE } from 'jgoboard/core'
import { createRenderer } from 'jgoboard/renderer'
import { kayaMedium } from 'jgoboard/presets'

export default function GoBoard({ stones, size = 19 }) {
  const containerRef = useRef(null)
  const rendererRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const base = window.location.origin + '/jgoboard/'

    const renderer = createRenderer(containerRef.current, {
      board: createBoard({ size }),
      theme: kayaMedium,
      assetBaseUrl: base,
      pixelRatio: 1,
    })
    rendererRef.current = renderer

    renderer.whenReady().then(() => renderer.render())

    return () => {
      renderer.destroy()
      rendererRef.current = null
    }
  }, [size])

  useEffect(() => {
    if (!rendererRef.current || !stones) return

    const board = createBoard({ size })
    if (stones.black) {
      for (const coord of stones.black) {
        try { board.setStone(coord, STONE.BLACK) } catch (e) {}
      }
    }
    if (stones.white) {
      for (const coord of stones.white) {
        try { board.setStone(coord, STONE.WHITE) } catch (e) {}
      }
    }
    rendererRef.current.setBoard(board)
    rendererRef.current.render()
  }, [stones, size])

  return (
    <div className="w-full flex justify-center overflow-hidden">
      <div ref={containerRef} className="max-w-full" />
    </div>
  )
}
