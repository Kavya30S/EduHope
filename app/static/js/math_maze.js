const config = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  scene: {
    preload: preload,
    create: create
  }
};

const game = new Phaser.Game(config);

function preload() {
  this.load.image('player', '/static/images/player.png');
}

function create() {
  this.add.image(400, 300, 'player');
}