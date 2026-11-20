plugins {
 id("com.android.application")
 id("org.jetbrains.kotlin.android")
 id("org.jetbrains.kotlin.plugin.compose")
}
android {
 namespace = "br.com.carbonapp.mobile"
 compileSdk = 35
 defaultConfig {
  applicationId = "br.com.carbonapp.mobile"
  minSdk = 26
  targetSdk = 35
  versionCode = 1
  versionName = "0.1.0"
  buildConfigField("String","API_BASE_URL","\"http://10.0.2.2:8080/\"")
 }
 buildFeatures { compose = true; buildConfig = true }
}
dependencies {
 implementation(platform("androidx.compose:compose-bom:2025.03.00"))
 implementation("androidx.activity:activity-compose:1.10.1")
 implementation("androidx.compose.ui:ui")
 implementation("androidx.compose.ui:ui-tooling-preview")
 implementation("androidx.compose.material3:material3")
 debugImplementation("androidx.compose.ui:ui-tooling")
}
