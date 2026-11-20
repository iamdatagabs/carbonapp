# CarbonApp Mobile — Android MVP
Native Android prototype using Kotlin and Jetpack Compose. The first screen captures project, sampling-point code, depth layer and field notes. Save currently validates and previews a draft in memory only; it does not persist or sync data.

Open `apps/mobile` as a Gradle project in Android Studio with JDK 17+ and Android SDK 35. Emulator API address for the next integration step: `http://10.0.2.2:8080/`.

Next: Room-backed offline drafts, Retrofit API client, idempotent sync queue, QR/barcode capture and explicit permission handling for optional location.
