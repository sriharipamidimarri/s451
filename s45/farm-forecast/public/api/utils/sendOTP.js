const nodemailer = require("nodemailer");
const OTP = require("../models/OTP"); // Path to OTP model
const crypto = require("crypto");

const sendOTP = async (email) => {
  const otp = crypto.randomInt(100000, 999999).toString(); // Generate a 6-digit OTP
  const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // Set OTP expiration (10 minutes)

  // Save OTP to the database
  await OTP.findOneAndUpdate(
    { email },
    { otp, expiresAt },
    { upsert: true, new: true }
  );
  

  // Configure Nodemailer
  const transporter = nodemailer.createTransport({
    service: "Gmail", // Or your email provider
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    }
  });

  // Email options
  const mailOptions = {
    from: "Farm-ForeCast OTp Verif",
    to: email,
    subject: "Your OTP Code",
    text: `Your OTP is ${otp}. It is valid for 10 minutes.`
  };

  // Send the email
  await transporter.sendMail(mailOptions);
};

module.exports = sendOTP;