import importlib.util
from pathlib import Path
import json
from datetime import datetime, timezone


def load_module(filename, module_name):
    file_path = Path(__file__).parent / "modules" / filename

    spec = importlib.util.spec_from_file_location(
        module_name,
        file_path
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# Load analyzer files
ec2_analyzer = load_module(
    "EC2-analyzer.py",
    "ec2_analyzer"
)

ebs_analyzer = load_module(
    "EBS-analyzer.py",
    "ebs_analyzer"
)

s3_analyzer = load_module(
    "s3-analyzer.py",
    "s3_analyzer"
)


def main():

    print("=" * 60)
    print("             AWS CLOUD COST OPTIMIZER")
    print("=" * 60)

    # ========================================
    # EC2
    # ========================================

    # ========================================
# EC2
# ========================================

print("\nEC2 INSTANCES")
print("-" * 60)

instances = ec2_analyzer.get_ec2_instances()

if not instances:

    print("No EC2 instances found.")

else:

    for instance in instances:

        print(
            f"ID: {instance['id']} | "
            f"Type: {instance['type']} | "
            f"State: {instance['state']} | "
            f"AZ: {instance['az']}"
        )

        # Only analyze running instances
        if instance["state"] == "running":

            cpu = ec2_analyzer.get_cpu_utilization(
                instance["id"]
            )

            print("  CPU ANALYSIS")

            if cpu is None:

                print("  Average CPU: No data available")

            else:

                print(
                    f"  Average CPU (7 days): "
                    f"{cpu}%"
                )

                analysis = ec2_analyzer.analyze_cpu(
                    instance["id"],
                    cpu
                )

                print(
                    f"  Status: "
                    f"{analysis['status']}"
                )

                print(
                    f"  Recommendation: "
                    f"{analysis['recommendation']}"
                )

    # ========================================
    # EBS
    # ========================================

    print("\nEBS VOLUMES")
    print("-" * 60)

    volumes = ebs_analyzer.get_ebs_volumes()

    potential_savings = 0

    if not volumes:

        print("No EBS volumes found.")

    else:

        for volume in volumes:

            if volume["attached"]:
                status = "ATTACHED"

            else:
                status = "UNATTACHED"

            print(
                f"ID: {volume['id']} | "
                f"Size: {volume['size']} GB | "
                f"Type: {volume['type']} | "
                f"Status: {status}"
            )

            # Detect unused EBS volumes
            if not volume["attached"]:

                print("  WARNING: POTENTIAL COST WASTE")
                print(
                    "  Recommendation: "
                    "Review and delete if unused."
                )

                # Estimated storage cost
                if volume["type"] == "gp3":

                    estimated_saving = (
                        volume["size"] * 0.08
                    )

                else:

                    estimated_saving = (
                        volume["size"] * 0.10
                    )

                potential_savings += estimated_saving

                print(
                    f"  Estimated monthly saving: "
                    f"${estimated_saving:.2f}"
                )

    # ========================================
    # S3
    # ========================================

    # ========================================
# S3
# ========================================

print("\nS3 BUCKETS")
print("-" * 60)

buckets = s3_analyzer.get_s3_buckets()

if not buckets:

    print("No S3 buckets found.")

else:

    for bucket in buckets:

        print(
            f"\nBucket: {bucket['name']}"
        )

        print(
            f"Created: {bucket['created']}"
        )

        storage = s3_analyzer.get_bucket_storage(
            bucket["name"]
        )

        if storage["error"]:

            print(
                "Storage analysis failed:"
            )

            print(
                storage["error"]
            )

        else:

            print(
                f"Storage: "
                f"{storage['size_gb']} GB"
            )

            print(
                f"Objects: "
                f"{storage['object_count']}"
            )

            if storage["size_gb"] > 10:

                print(
                    "  WARNING: Large S3 bucket"
                )

                print(
                    "  Recommendation: "
                    "Review storage classes and "
                    "lifecycle policies."
                )

            else:

                print(
                    "  Status: Storage usage appears low."
                )

    # ========================================
    # COST OPTIMIZATION SUMMARY
    # ========================================

    print("\nCOST OPTIMIZATION SUMMARY")
    print("-" * 60)

    if potential_savings > 0:

        print(
            f"Potential monthly savings: "
            f"${potential_savings:.2f}"
        )

    else:

        print("No obvious EBS savings detected.")

    # ========================================
    # OPTIMIZATION RECOMMENDATIONS
    # ========================================

    print("\nOPTIMIZATION RECOMMENDATIONS")
    print("-" * 60)

    recommendations = []

    # EC2 recommendations
    for instance in instances:

        if instance["state"] == "running":

            cpu = ec2_analyzer.get_cpu_utilization(
                instance["id"]
            )

            if cpu is not None:

                if cpu < 10:

                    recommendations.append({
                        "resource": instance["id"],
                        "service": "EC2",
                        "priority": "HIGH",
                        "issue": f"Very low CPU utilization ({cpu}%)",
                        "recommendation":
                            "Consider stopping the instance "
                            "when not required or scheduling "
                            "automatic start/stop."
                    })

                elif cpu < 30:

                    recommendations.append({
                        "resource": instance["id"],
                        "service": "EC2",
                        "priority": "MEDIUM",
                        "issue": f"Low CPU utilization ({cpu}%)",
                        "recommendation":
                            "Review whether a smaller instance "
                            "type could handle the workload."
                    })

    # EBS recommendations
    for volume in volumes:

        if not volume["attached"]:

            recommendations.append({
                "resource": volume["id"],
                "service": "EBS",
                "priority": "HIGH",
                "issue": "Unattached EBS volume",
                "recommendation":
                    "Review the volume and delete it if "
                    "the data is no longer required."
            })

    # S3 recommendations
    for bucket in buckets:

        storage = s3_analyzer.get_bucket_storage(
            bucket["name"]
        )

        if storage["error"] is None:

            if storage["size_gb"] > 10:

                recommendations.append({
                    "resource": bucket["name"],
                    "service": "S3",
                    "priority": "MEDIUM",
                    "issue":
                        f"Large storage usage "
                        f"({storage['size_gb']} GB)",
                    "recommendation":
                        "Review S3 storage classes and "
                        "lifecycle policies."
                })

    # Display recommendations
    if not recommendations:

        print("No optimization recommendations found.")

    else:

        for index, recommendation in enumerate(
            recommendations,
            start=1
        ):

            print(
                f"\n{index}. "
                f"[{recommendation['priority']}] "
                f"{recommendation['service']}"
            )

            print(
                f"   Resource: "
                f"{recommendation['resource']}"
            )

            print(
                f"   Issue: "
                f"{recommendation['issue']}"
            )

            print(
                f"   Recommendation: "
                f"{recommendation['recommendation']}"
            )

    print("\n" + "=" * 60)
    print("Resource scan completed.")
    print("=" * 60)

        # ========================================
    # COST HEALTH SCORE
    # ========================================

    score = 100

    high_priority = 0
    medium_priority = 0
    low_priority = 0

    for recommendation in recommendations:

        priority = recommendation["priority"]

        if priority == "HIGH":

            high_priority += 1
            score -= 25

        elif priority == "MEDIUM":

            medium_priority += 1
            score -= 10

        elif priority == "LOW":

            low_priority += 1
            score -= 5

    # Prevent score from going below zero
    score = max(score, 0)

    print("\nCLOUD COST HEALTH SCORE")
    print("-" * 60)

    print(f"Score: {score} / 100")

    print("\nIssue Summary:")
    print(f"  High Priority: {high_priority}")
    print(f"  Medium Priority: {medium_priority}")
    print(f"  Low Priority: {low_priority}")

    if score >= 80:

        print("\nStatus: HEALTHY")

    elif score >= 60:

        print("\nStatus: NEEDS REVIEW")

    else:

        print("\nStatus: HIGH OPTIMIZATION NEEDED")
    # ========================================
    # GENERATE JSON REPORT
    # ========================================

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ec2_instances": instances,
        "ebs_volumes": volumes,
        "s3_buckets": buckets,
        "recommendations": recommendations
    }

    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    report_file = reports_dir / "aws_cost_report.json"

    with open(report_file, "w", encoding="utf-8") as file:

        json.dump(
            report,
            file,
            indent=4,
            default=str
        )

    print("\nREPORT GENERATED")
    print("-" * 60)
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()