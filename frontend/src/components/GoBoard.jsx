import { useEffect, useRef, useState } from 'react'
import { createBoard, STONE, createRenderer } from 'jgoboard'

export default function GoBoard({ stones, size = 19, lastMove }) {
  const containerRef = useRef(null)
  const rendererRef = useRef(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!containerRef.current) return

    containerRef.current.innerHTML = ''

    const board = createBoard({ size })

    if (stones?.black) {
      for (const coord of stones.black) {
        try {
          board.setStone(coord, STONE.BLACK)
        } catch (e) {}
      }
    }
    if (stones?.white) {
      for (const coord of stones.white) {
        try {
          board.setStone(coord, STONE.WHITE)
        } catch (e) {}
      }
    }

    if (rendererRef.current) {
      rendererRef.current.destroy()
    }

    const renderer = createRenderer(containerRef.current, {
      board,
      theme: 'bw-medium',
      layout: {
        padding: { normal: 6, clipped: 4 },
        border: { color: '#6b5a3e', lineWidth: 1.5 },
        grid: { color: '#8a7548', x: 20, y: 20, smooth: 0.5, borderWidth: 2, lineWidth: 1 },
        stars: { points: 'auto', offset: 'auto', radius: 3 },
        coordinates: false,
        mark: { lineWidth: 1.5, blackColor: '#ffffff', whiteColor: '#1a1a1a', clearColor: '#ffffff', font: '10px sans-serif' },
        shadow: { xOff: 2, yOff: 2 },
        stone: { radius: 9, dimAlpha: 0.3 },
        boardShadow: { color: 'rgba(0,0,0,0.3)', blur: 10, offX: 4, offY: 4 },
        margin: { color: '#3d2b1a', normal: 20, clipped: 12 },
        textures: false,
      },
    })

    rendererRef.current = renderer

    renderer.whenReady().then(() => {
      setReady(true)
      renderer.render()
    })

    return () => {
      if (rendererRef.current) {
        rendererRef.current.destroy()
        rendererRef.current = null
      }
    }
  }, [stones, size])

  return (
    <div className="w-full flex justify-center">
      <div
        ref={containerRef}
        className={`transition-opacity duration-500 ${ready ? 'opacity-100' : 'opacity-0'}`}
      />
    </div>
  )
}
