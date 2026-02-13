plugins {
    kotlin("jvm") version "1.9.22" apply false
    kotlin("plugin.serialization") version "1.9.22" apply false
}

group = "com.gok"
version = "0.1.0"

allprojects {
    repositories {
        mavenCentral()
    }
}
