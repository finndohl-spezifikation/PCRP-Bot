# ── Build-Stage ──────────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
# Abhängigkeiten vorab laden (besseres Layer-Caching)
COPY pom.xml .
RUN mvn dependency:go-offline -q
# Quellcode kompilieren und Fat-JAR erzeugen
COPY src ./src
RUN mvn package -DskipTests -q

# ── Runtime-Stage ─────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
# Persistentes Datenverzeichnis (wird von Railway als Volume gemountet)
RUN mkdir -p /app/data
COPY --from=build /app/target/pcrp-bot.jar app.jar
# PORT wird von Railway automatisch gesetzt; der Web-Server lauscht darauf
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
