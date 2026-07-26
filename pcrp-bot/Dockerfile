# ── Build-Stage ──────────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pcrp-bot/pom.xml .
RUN mvn dependency:go-offline -q
COPY pcrp-bot/src ./src
RUN mvn package -DskipTests -q

# ── Runtime-Stage ─────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN mkdir -p /app/data
COPY --from=build /app/target/pcrp-bot.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
