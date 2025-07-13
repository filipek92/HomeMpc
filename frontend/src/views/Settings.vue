<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="settings-header">
      <q-toolbar>
        <q-btn flat dense icon="arrow_back" @click="$router.push('/')" />
        <q-toolbar-title>
          <q-icon name="fas fa-cog" class="q-mr-sm" />
          Nastavení PowerStreamPlan
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <q-page class="settings-page">
        <div class="settings-container">
          <q-card class="settings-card">
            <q-card-section>
              <div class="text-h6">Nastavení aplikace</div>
              <div class="text-subtitle2 text-grey-6">
                Konfigurace systému bude implementována v dalších verzích
              </div>
            </q-card-section>

            <q-separator />

            <q-card-section>
              <q-btn
                color="primary"
                icon="home"
                label="Zpět na dashboard"
                @click="$router.push('/')"
              />
            </q-card-section>
          </q-card>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
// Settings page - placeholder for future implementation
</script>

<style lang="scss" scoped>
.settings-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.settings-card {
  border-radius: 1rem;
}

.settings-header {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
}
</style>
