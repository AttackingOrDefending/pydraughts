from draughts import Board, Move
from draughts.svg import create_svg


def test_svg():
    board = Board(fen="W:WK4,19,27,33,34,47:B11,12,17,22,25,26:H0:F50")
    board.push(Move(board, pdn_move="27x16"))
    svg = create_svg(board)
    assert svg == """<svg viewBox="0 0 432 432" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="432" height="432" fill="#1A1A1A"/>
<text x="36.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">a</text>
<text x="76.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">b</text>
<text x="116.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">c</text>
<text x="156.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">d</text>
<text x="196.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">e</text>
<text x="236.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">f</text>
<text x="276.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">g</text>
<text x="316.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">h</text>
<text x="356.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">i</text>
<text x="396.0" y="428.0" text-anchor="middle" font-size="12.8" fill="white">j</text>
<text x="8.0" y="36.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">10</text>
<text x="8.0" y="76.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">9</text>
<text x="8.0" y="116.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">8</text>
<text x="8.0" y="156.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">7</text>
<text x="8.0" y="196.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">6</text>
<text x="8.0" y="236.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">5</text>
<text x="8.0" y="276.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">4</text>
<text x="8.0" y="316.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">3</text>
<text x="8.0" y="356.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">2</text>
<text x="8.0" y="396.0" text-anchor="middle" dominant-baseline="central" font-size="12.8" fill="white">1</text>
<rect x="16" y="16" width="40" height="40" fill="#E8D0AA"/>
<rect x="56" y="16" width="40" height="40" fill="#B87C4C"/>
<rect x="96" y="16" width="40" height="40" fill="#E8D0AA"/>
<rect x="136" y="16" width="40" height="40" fill="#B87C4C"/>
<rect x="176" y="16" width="40" height="40" fill="#E8D0AA"/>
<rect x="216" y="16" width="40" height="40" fill="#B87C4C"/>
<rect x="256" y="16" width="40" height="40" fill="#E8D0AA"/>
<rect x="296" y="16" width="40" height="40" fill="#B87C4C"/>
<rect x="336" y="16" width="40" height="40" fill="#E8D0AA"/>
<rect x="376" y="16" width="40" height="40" fill="#B87C4C"/>
<rect x="16" y="56" width="40" height="40" fill="#B87C4C"/>
<rect x="56" y="56" width="40" height="40" fill="#E8D0AA"/>
<rect x="96" y="56" width="40" height="40" fill="#B87C4C"/>
<rect x="136" y="56" width="40" height="40" fill="#E8D0AA"/>
<rect x="176" y="56" width="40" height="40" fill="#B87C4C"/>
<rect x="216" y="56" width="40" height="40" fill="#E8D0AA"/>
<rect x="256" y="56" width="40" height="40" fill="#B87C4C"/>
<rect x="296" y="56" width="40" height="40" fill="#E8D0AA"/>
<rect x="336" y="56" width="40" height="40" fill="#B87C4C"/>
<rect x="376" y="56" width="40" height="40" fill="#E8D0AA"/>
<rect x="16" y="96" width="40" height="40" fill="#E8D0AA"/>
<rect x="56" y="96" width="40" height="40" fill="#B87C4C"/>
<rect x="96" y="96" width="40" height="40" fill="#E8D0AA"/>
<rect x="136" y="96" width="40" height="40" fill="#B87C4C"/>
<rect x="176" y="96" width="40" height="40" fill="#E8D0AA"/>
<rect x="216" y="96" width="40" height="40" fill="#B87C4C"/>
<rect x="256" y="96" width="40" height="40" fill="#E8D0AA"/>
<rect x="296" y="96" width="40" height="40" fill="#B87C4C"/>
<rect x="336" y="96" width="40" height="40" fill="#E8D0AA"/>
<rect x="376" y="96" width="40" height="40" fill="#B87C4C"/>
<rect x="16" y="136" width="40" height="40" fill="#B87C4C"/>
<rect x="56" y="136" width="40" height="40" fill="#E8D0AA"/>
<rect x="96" y="136" width="40" height="40" fill="#B87C4C"/>
<rect x="136" y="136" width="40" height="40" fill="#E8D0AA"/>
<rect x="176" y="136" width="40" height="40" fill="#B87C4C"/>
<rect x="216" y="136" width="40" height="40" fill="#E8D0AA"/>
<rect x="256" y="136" width="40" height="40" fill="#B87C4C"/>
<rect x="296" y="136" width="40" height="40" fill="#E8D0AA"/>
<rect x="336" y="136" width="40" height="40" fill="#B87C4C"/>
<rect x="376" y="136" width="40" height="40" fill="#E8D0AA"/>
<rect x="16" y="176" width="40" height="40" fill="#E8D0AA"/>
<rect x="56" y="176" width="40" height="40" fill="#B87C4C"/>
<rect x="96" y="176" width="40" height="40" fill="#E8D0AA"/>
<rect x="136" y="176" width="40" height="40" fill="#B87C4C"/>
<rect x="176" y="176" width="40" height="40" fill="#E8D0AA"/>
<rect x="216" y="176" width="40" height="40" fill="#B87C4C"/>
<rect x="256" y="176" width="40" height="40" fill="#E8D0AA"/>
<rect x="296" y="176" width="40" height="40" fill="#B87C4C"/>
<rect x="336" y="176" width="40" height="40" fill="#E8D0AA"/>
<rect x="376" y="176" width="40" height="40" fill="#B87C4C"/>
<rect x="16" y="216" width="40" height="40" fill="#B87C4C"/>
<rect x="56" y="216" width="40" height="40" fill="#E8D0AA"/>
<rect x="96" y="216" width="40" height="40" fill="#B87C4C"/>
<rect x="136" y="216" width="40" height="40" fill="#E8D0AA"/>
<rect x="176" y="216" width="40" height="40" fill="#B87C4C"/>
<rect x="216" y="216" width="40" height="40" fill="#E8D0AA"/>
<rect x="256" y="216" width="40" height="40" fill="#B87C4C"/>
<rect x="296" y="216" width="40" height="40" fill="#E8D0AA"/>
<rect x="336" y="216" width="40" height="40" fill="#B87C4C"/>
<rect x="376" y="216" width="40" height="40" fill="#E8D0AA"/>
<rect x="16" y="256" width="40" height="40" fill="#E8D0AA"/>
<rect x="56" y="256" width="40" height="40" fill="#B87C4C"/>
<rect x="96" y="256" width="40" height="40" fill="#E8D0AA"/>
<rect x="136" y="256" width="40" height="40" fill="#B87C4C"/>
<rect x="176" y="256" width="40" height="40" fill="#E8D0AA"/>
<rect x="216" y="256" width="40" height="40" fill="#B87C4C"/>
<rect x="256" y="256" width="40" height="40" fill="#E8D0AA"/>
<rect x="296" y="256" width="40" height="40" fill="#B87C4C"/>
<rect x="336" y="256" width="40" height="40" fill="#E8D0AA"/>
<rect x="376" y="256" width="40" height="40" fill="#B87C4C"/>
<rect x="16" y="296" width="40" height="40" fill="#B87C4C"/>
<rect x="56" y="296" width="40" height="40" fill="#E8D0AA"/>
<rect x="96" y="296" width="40" height="40" fill="#B87C4C"/>
<rect x="136" y="296" width="40" height="40" fill="#E8D0AA"/>
<rect x="176" y="296" width="40" height="40" fill="#B87C4C"/>
<rect x="216" y="296" width="40" height="40" fill="#E8D0AA"/>
<rect x="256" y="296" width="40" height="40" fill="#B87C4C"/>
<rect x="296" y="296" width="40" height="40" fill="#E8D0AA"/>
<rect x="336" y="296" width="40" height="40" fill="#B87C4C"/>
<rect x="376" y="296" width="40" height="40" fill="#E8D0AA"/>
<rect x="16" y="336" width="40" height="40" fill="#E8D0AA"/>
<rect x="56" y="336" width="40" height="40" fill="#B87C4C"/>
<rect x="96" y="336" width="40" height="40" fill="#E8D0AA"/>
<rect x="136" y="336" width="40" height="40" fill="#B87C4C"/>
<rect x="176" y="336" width="40" height="40" fill="#E8D0AA"/>
<rect x="216" y="336" width="40" height="40" fill="#B87C4C"/>
<rect x="256" y="336" width="40" height="40" fill="#E8D0AA"/>
<rect x="296" y="336" width="40" height="40" fill="#B87C4C"/>
<rect x="336" y="336" width="40" height="40" fill="#E8D0AA"/>
<rect x="376" y="336" width="40" height="40" fill="#B87C4C"/>
<rect x="16" y="376" width="40" height="40" fill="#B87C4C"/>
<rect x="56" y="376" width="40" height="40" fill="#E8D0AA"/>
<rect x="96" y="376" width="40" height="40" fill="#B87C4C"/>
<rect x="136" y="376" width="40" height="40" fill="#E8D0AA"/>
<rect x="176" y="376" width="40" height="40" fill="#B87C4C"/>
<rect x="216" y="376" width="40" height="40" fill="#E8D0AA"/>
<rect x="256" y="376" width="40" height="40" fill="#B87C4C"/>
<rect x="296" y="376" width="40" height="40" fill="#E8D0AA"/>
<rect x="336" y="376" width="40" height="40" fill="#B87C4C"/>
<rect x="376" y="376" width="40" height="40" fill="#E8D0AA"/>
<circle cx="316" cy="36" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
<defs>
    <linearGradient id="crown_gradient_316_36" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
        <stop offset="50%" style="stop-color:#FFA500;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#FFD700;stop-opacity:1" />
    </linearGradient>
</defs>
<path d="M 316.0,28.0 L 317.7962717310058,33.52764406519016 L 323.60845213036123,33.52786404500042 L 318.906428713798,36.94435593480984 L 320.70228201833976,42.47213595499958 L 316.0,39.056 L 311.29771798166024,42.47213595499958 L 313.093571286202,36.94435593480984 L 308.39154786963877,33.52786404500042 L 314.2037282689942,33.52764406519016 Z" fill="url(#crown_gradient_316_36)" stroke="#DAA520" stroke-width="2"/>
<circle cx="36" cy="156" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
<circle cx="116" cy="156" r="16.0" fill="#000000" stroke="#FFFFFF" stroke-width="2"/>
<circle cx="276" cy="156" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
<circle cx="396" cy="196" r="16.0" fill="#000000" stroke="#FFFFFF" stroke-width="2"/>
<circle cx="36" cy="236" r="16.0" fill="#000000" stroke="#FFFFFF" stroke-width="2"/>
<circle cx="236" cy="276" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
<circle cx="316" cy="276" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
<circle cx="116" cy="396" r="16.0" fill="#FFFFFF" stroke="#000000" stroke-width="2"/>
</svg>"""
