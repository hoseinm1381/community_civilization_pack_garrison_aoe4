// Code-native SVG assets; PNG byte payloads referenced directly by official XAML URI convention.
const path = require('path');
const sharp = require('C:/Users/RS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = path.resolve(__dirname, '../..');
const folder = path.join(root, 'assets/ui/images/vietnam_0710');
const masters = path.join(root, 'art/authoring/release_0710/hud');
(async () => {
  for (const name of ['dai_viet_dragon', 'buffalo']) {
    await sharp(path.join(masters, name+'.svg')).png().toFile(path.join(folder,name+'.png'));
  }
  await sharp(path.join(masters,'dai_viet_dragon.svg')).resize(32,18).png().toFile(path.join(root,'output/release_0710/hud/flag_actual_32x18.png'));
  await sharp(path.join(masters,'dai_viet_dragon.svg')).resize(32,18).resize(512,288,{kernel:'nearest'}).png().toFile(path.join(root,'output/release_0710/hud/flag_preview.png'));
})();
