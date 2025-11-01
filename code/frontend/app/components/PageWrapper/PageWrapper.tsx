import classes from "./PageWrapper.module.css";

interface AppPageProps {
  children: React.ReactNode;
}

export default function PageWrapper({ children }: AppPageProps) {
  return (
    <div className={classes.pageWrapper}>
      <div className={classes.innerWrapper}>
        <div className={classes.contentWrapper}>{children}</div>
      </div>
    </div>
  );
}
