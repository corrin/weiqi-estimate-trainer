import { useEffect, useRef } from 'react'
import { createBoard, STONE, createRenderer } from 'jgoboard'

export default function GoBoard({ stones, size = 19 }) {
  const containerRef = useRef(null)
  const rendererRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const renderer = createRenderer(containerRef.current, {
      board: createBoard({ size }),
      theme: 'kaya-medium',
      assetBaseUrl: '/jgoboard/',
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
