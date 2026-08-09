# ── Build-Stage ──────────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pcrp-bot/pom.xml .
RUN mvn dependency:go-offline -q
COPY pcrp-bot/src ./src
RUN mvn package -DskipTests -q

# ── Runtime-Stage ─────────────────────────────────────────────────────────────
# glibc-basiert (jammy), damit opus-java (Audio-Encoding) und espeak-ng (TTS) funktionieren
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app/data
COPY --from=build /app/target/pcrp-bot.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
