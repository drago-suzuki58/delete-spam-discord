import asyncio
import sys

import discord
from loguru import logger

import del_spam.config as config
from del_spam.deleter import MessageDeleter
from del_spam.filter import FilterEngine


async def main():
    logger.add("logs/file_{time}.log", rotation="1 week", enqueue=True)
    logger.info("=== Discord Message Deleter ===")

    filter_engine = FilterEngine()
    filter_engine.load_all_rules(config.DELETE_RULES)

    print("\n=== Available Rules ===")
    enabled_rules = [
        name for name, rule in config.DELETE_RULES.items() if rule.get("enabled", False)
    ]

    if not enabled_rules:
        logger.warning("No enabled rules found")
        print("No enabled rules. Please enable a rule in config.py")
        return

    for i, rule_name in enumerate(enabled_rules, 1):
        rule = config.DELETE_RULES[rule_name]
        print(f"{i}. {rule_name}: {rule.get('description', 'No description')}")

    print(f"{len(enabled_rules) + 1}. Exit")

    while True:
        try:
            choice = input("\nSelect rule to execute (number): ").strip()
            choice_num = int(choice)

            if choice_num == len(enabled_rules) + 1:
                logger.info("Exiting...")
                return

            if 1 <= choice_num <= len(enabled_rules):
                selected_rule = enabled_rules[choice_num - 1]
                break
            else:
                print(f"Please select a number between 1 and {len(enabled_rules) + 1}")
        except ValueError:
            print("Invalid input. Please enter a number.")

    rule_config = config.DELETE_RULES[selected_rule]
    print("\n=== Confirmation ===")
    print(f"Rule: {selected_rule}")
    print(f"Description: {rule_config.get('description', 'No description')}")
    print(f"Dry Run: {config.DRY_RUN}")
    print(f"Max Deletions: {config.MAX_DELETIONS_PER_RUN}")

    if config.DRY_RUN:
        print("\nThis is a DRY RUN - no messages will actually be deleted")
    else:
        print("\nWARNING: This will actually delete messages!")

    confirm = input("\nContinue? (yes/no): ").strip().lower()
    while True:
        if confirm in ["yes", "y"]:
            break
        elif confirm in ["no", "n"]:
            logger.info("Operation cancelled by user")
            return
        else:
            print("invalid input. Please enter 'yes' or 'no'")
            break

    logger.info("Connecting to Discord...")
    bot = discord.Client(intents=discord.Intents.default())

    deleter = MessageDeleter(filter_engine)

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user}")

        deleted_count = await deleter.delete_by_rule(bot, selected_rule)
        logger.info(f"Total deleted: {deleted_count}")

        await bot.close()

    await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
