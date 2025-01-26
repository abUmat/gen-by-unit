resource "aws_lambda_function" "gen_by_unit" {
  function_name = "prd-hobby-gen_by_unit"
  architectures = ["x86_64"]
  runtime       = var.python_runtime
  filename      = "lambda.zip"
  package_type  = "Zip"
  handler       = "main.handler"
  memory_size   = 128
  timeout       = 900
  role          = aws_iam_role.gen_by_unit.arn

  environment {
    variables = {
      "IMG_PATH" = "/tmp/img"
    }
  }
  layers = [
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p310-requests:17",
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p310-matplotlib:2",
  ]
}

resource "aws_iam_role" "gen_by_unit" {
  name               = "prd-hobby-gen_by_unit"
  assume_role_policy = file("assume_role/lambda.json")
}

resource "aws_iam_policy" "gen_by_unit" {
  name   = "prd-hobby-gen_by_unit"
  policy = data.aws_iam_policy_document.gen_by_unit.json
}

data "aws_iam_policy_document" "gen_by_unit" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.gen_by_unit.arn}:*"]
  }
}

resource "aws_cloudwatch_log_group" "gen_by_unit" {
  name              = "/aws/lambda/prd-hobby-gen_by_unit"
  retention_in_days = 7
}

resource "aws_iam_role_policy_attachment" "gen_by_unit" {
  role       = aws_iam_role.gen_by_unit.id
  policy_arn = aws_iam_policy.gen_by_unit.arn
}

resource "aws_cloudwatch_event_rule" "gen_by_unit_cron_trigger" {
  name                = "prd-hobby-gen_by_unit_cron_trigger"
  schedule_expression = "cron(0 7 * * ? *)" # 毎日UTC時間の07:00 == JTC時間の16:00に実行
}

resource "aws_cloudwatch_event_target" "gen_by_unit_cron_trigger" {
  rule = aws_cloudwatch_event_rule.gen_by_unit_cron_trigger.name
  arn  = aws_lambda_function.gen_by_unit.arn
}

resource "aws_lambda_permission" "gen_by_unit_cron_trigger_invoke_lambda" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gen_by_unit.id
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.gen_by_unit_cron_trigger.arn
}



