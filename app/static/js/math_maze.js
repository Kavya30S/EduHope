const maze = [
    [1, 0, 1, 1],
    [1, 0, 0, 1],
    [1, 1, 0, 1],
    [0, 0, 0, 2]
];
let playerPos = [0, 0];

function renderMaze() {
    const mazeDiv = document.getElementById("maze");
    mazeDiv.innerHTML = "";
    maze.forEach((row, y) => {
        const rowDiv = document.createElement("div");
        row.forEach((cell, x) => {
            const cellDiv = document.createElement("div");
            cellDiv.className = "cell " + (cell === 1 ? "wall" : cell === 2 ? "goal" : "path");
            if (x === playerPos[1] && y === playerPos[0]) cellDiv.classList.add("player");
            rowDiv.appendChild(cellDiv);
        });
        mazeDiv.appendChild(rowDiv);
    });
}

function movePlayer(direction) {
    const [y, x] = playerPos;
    let newY = y, newX = x;
    if (direction === "up") newY--;
    else if (direction === "down") newY++;
    else if (direction === "left") newX--;
    else if (direction === "right") newX++;

    if (maze[newY] && maze[newY][newX] !== 1) {
        playerPos = [newY, newX];
        renderMaze();
        if (maze[newY][newX] === 2) alert("You won!");
    }
}

document.addEventListener("keydown", e => {
    const moves = { "ArrowUp": "up", "ArrowDown": "down", "ArrowLeft": "left", "ArrowRight": "right" };
    if (moves[e.key]) movePlayer(moves[e.key]);
});

document.addEventListener("DOMContentLoaded", renderMaze);