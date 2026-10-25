import { defineConfig } from 'vite';

export default defineConfig({
    base: './',
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    phaser: ['phaser']
                }
            }
        },
    },
    server: {
        port: 8080,
        // Blender saves and backs up .blend files under art/ while the game runs; watching them
        // crashed the dev server (EBUSY). The game only reads src/ and public/.
        watch: { ignored: ['**/art/**', '**/field/**', '**/review/**', '**/docs/**'] }
    }
});
