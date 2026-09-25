; ModuleID = 'guarded_mul_add.cu'
source_filename = "guarded_mul_add.cu"
target datalayout = "e-p6:32:32-i64:64-i128:128-v16:16-v32:32-n16:32:64"
target triple = "nvptx64-nvidia-cuda"

; Function Attrs: mustprogress nofree noinline norecurse nosync nounwind willreturn memory(argmem: readwrite)
define dso_local ptx_kernel void @guarded_mul_add(ptr noundef readonly captures(none) %0, ptr noundef readonly captures(none) %1, ptr noundef readonly captures(none) %2, ptr noundef writeonly captures(none) %3, i32 noundef %4) local_unnamed_addr #0 {
  %6 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.ctaid.x()
  %7 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.ntid.x()
  %8 = mul i32 %6, %7
  %9 = tail call noundef i32 @llvm.nvvm.read.ptx.sreg.tid.x()
  %10 = add i32 %8, %9
  %11 = icmp slt i32 %10, %4
  br i1 %11, label %12, label %27

12:                                               ; preds = %5
  %13 = sext i32 %10 to i64
  %14 = getelementptr inbounds float, ptr %0, i64 %13
  %15 = load float, ptr %14, align 4, !tbaa !8
  %16 = fcmp uno float %15, 0.000000e+00
  br i1 %16, label %24, label %17

17:                                               ; preds = %12
  %18 = getelementptr inbounds float, ptr %1, i64 %13
  %19 = load float, ptr %18, align 4, !tbaa !8
  %20 = fmul float %15, %19
  %21 = getelementptr inbounds float, ptr %2, i64 %13
  %22 = load float, ptr %21, align 4, !tbaa !8
  %23 = fadd float %20, %22
  br label %24

24:                                               ; preds = %12, %17
  %25 = phi float [ %23, %17 ], [ 0.000000e+00, %12 ]
  %26 = getelementptr inbounds float, ptr %3, i64 %13
  store float %25, ptr %26, align 4, !tbaa !8
  br label %27

27:                                               ; preds = %24, %5
  ret void
}

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 0, 2147483647) i32 @llvm.nvvm.read.ptx.sreg.ctaid.x() #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 1, 1025) i32 @llvm.nvvm.read.ptx.sreg.ntid.x() #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare noundef range(i32 0, 1024) i32 @llvm.nvvm.read.ptx.sreg.tid.x() #1

attributes #0 = { mustprogress nofree noinline norecurse nosync nounwind willreturn memory(argmem: readwrite) "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="sm_89" "target-features"="+ptx84,+sm_89" "uniform-work-group-size"="true" }
attributes #1 = { mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0, !1, !2, !3}
!nvvm.annotations = !{!4}
!llvm.ident = !{!5, !6}
!nvvmir.version = !{!7}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 12, i32 4]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 4, !"nvvm-reflect-ftz", i32 0}
!3 = !{i32 7, !"frame-pointer", i32 2}
!4 = !{ptr @guarded_mul_add}
!5 = !{!"Ubuntu clang version 21.1.8 (++20251221032842+2078da43e25a-1~exp1~20251221153008.77)"}
!6 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
!7 = !{i32 2, i32 0}
!8 = !{!9, !9, i64 0}
!9 = !{!"float", !10, i64 0}
!10 = !{!"omnipotent char", !11, i64 0}
!11 = !{!"Simple C++ TBAA"}
